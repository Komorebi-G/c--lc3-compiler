from __future__ import annotations

import os
import pty
import re
import select
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = ROOT / "tests" / "cases"
GOLDEN_DIR = ROOT / "tests" / "golden"
BUILD_DIR = ROOT / "tests" / "build"
LC3TOOLS_DIR = ROOT / "lc3tools"
COMPILER_CMD = [sys.executable, "-m", "compiler_lc3"]
LC3AS = LC3TOOLS_DIR / "lc3as"
LC3SIM = LC3TOOLS_DIR / "lc3sim"

IS_CI = os.environ.get("CI", "").lower() in ("true", "1", "yes")


@dataclass
class Case:
    source: str
    expected_global: Optional[tuple[str, int]] = None
    expected_output: Optional[str] = None
    program_input: str = ""


CASES = [
    Case("if_else_chain.c", expected_global=("result", 2)),
    Case("while_break_continue.c", expected_global=("result", 13)),
    Case("for_and_call.c", expected_global=("result", 10)),
    Case("for_and_call_output.c", expected_output="6\n"),
    Case("multi_param_chain.c", expected_global=("result", 7)),
    Case("compare_matrix.c", expected_global=("result", 63)),
    Case("call_in_condition.c", expected_global=("result", 2)),
    Case("deep_add_chain_output.c", expected_output="E\n"),
    Case("five_param_sum_output.c", expected_output="?\n"),
    Case("call_chain_output.c", expected_output="9\n"),
    Case("inc_dec_semantics_output.c", expected_output="34555433\n"),
    Case("inc_dec_call_loop_output.c", expected_output="334\n"),
    Case("loop_accumulate_output.c", expected_output=":\n"),
    Case("branch_call_mix_output.c", expected_output="4\n"),
    Case("nested_blocks.c", expected_global=("result", 2)),
    Case("puts_putchar.c", expected_output="OK\nA\n"),
    Case("getchar_echo.c", expected_output="ab\n", program_input="ab\n"),
    Case("getchar_count_a.c", expected_output="3\n", program_input="abaca\n"),
    Case("logical_and.c", expected_global=("result", 1)),
    Case("logical_or.c", expected_global=("result", 2)),
    Case("logical_precedence.c", expected_global=("result", 2)),
    Case("multiply.c", expected_global=("result", 43)),
    Case("divide_mod.c", expected_global=("result", 0)),
    Case("array_basic.c", expected_global=("result", 60)),
    Case("pointer_basic.c", expected_global=("result", 99)),
    Case("mul_edge.c", expected_output="1111\n"),
    Case("div_edge.c", expected_output="111111\n"),
    Case("mod_edge.c", expected_output="111111\n"),
    Case("array_loop.c", expected_output="15\n"),
    Case("pointer_chain.c", expected_output="30\n"),
    Case("short_circuit.c", expected_output="000\n"),
    Case("short_circuit_left_effect.c", expected_output="12\n"),
    Case("precedence_full.c", expected_output="Y1Y1\n"),
    Case("types_basic.c", expected_global=("result", 107)),
    Case("types_ptr.c", expected_global=("result", 42)),
    Case("char_bool_logic_output.c", expected_output="A\n"),
    Case("compound_assign.c", expected_global=("result", 3)),
    Case("compound_array_ptr.c", expected_global=("out", 46)),
    Case("array_complex_index.c", expected_global=("out", 267)),
    Case("builtin_leaf_return.c", expected_output="A7\n"),
    Case("array_call_index.c", expected_output="7\n"),
    Case("array_init_call.c", expected_output="5\n"),
    Case("pointer_call_value.c", expected_output="9\n"),
]

BEG_CASES = [
    Case("beginner_loop_local.c", expected_output="3\n"),
    Case("beginner_nested_call.c", expected_output="5\n"),
    Case("beginner_global_local.c", expected_output="7\n"),
    Case("beginner_input_loop.c", expected_output="4\n", program_input="test\n"),
    Case("beginner_multi_func.c", expected_output="8\n"),
    Case("beginner_builtin_leaf.c", expected_output="B6\n"),
]


class TestFailure(RuntimeError):
    pass


def run(cmd: list[str], *, cwd: Path, input_text: str | None = None, timeout: int = 30) -> str:
    env = dict(os.environ)
    env["PATH"] = f"{ROOT / '.local' / 'bin'}:{env.get('PATH', '')}"
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        input=input_text,
        text=True,
        capture_output=True,
        env=env,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        raise TestFailure(
            f"command failed: {' '.join(cmd)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc.stdout + proc.stderr


def compile_to_asm(source: Path, output: Path, extra_flags: list[str] | None = None) -> str:
    """Compile a .c source to .asm; return the generated text."""
    cmd = COMPILER_CMD + [str(source), "-o", str(output)]
    if extra_flags:
        cmd.extend(extra_flags)
    run(cmd, cwd=ROOT)
    return output.read_text(encoding="utf-8")


def _diff_golden(label: str, generated: str, golden_path: Path) -> None:
    """Compare generated text against a golden file; raise TestFailure on mismatch."""
    if not golden_path.exists():
        raise TestFailure(
            f"{label}: golden file missing: {golden_path}\n"
            f"Run locally to regenerate golden files."
        )
    expected = golden_path.read_text(encoding="utf-8")
    if generated == expected:
        return
    gen_lines = generated.splitlines()
    exp_lines = expected.splitlines()
    for i, (g, e) in enumerate(zip(gen_lines, exp_lines), start=1):
        if g != e:
            raise TestFailure(
                f"{label}: output differs from golden at line {i}\n"
                f"  expected: {e}\n"
                f"  got:      {g}"
            )
    shorter = min(len(gen_lines), len(exp_lines))
    if len(gen_lines) > len(exp_lines):
        raise TestFailure(
            f"{label}: extra lines after golden EOF at line {shorter + 1}\n"
            f"  first extra: {gen_lines[shorter]}"
        )
    raise TestFailure(
        f"{label}: missing lines after generated EOF at line {shorter + 1}\n"
        f"  first missing: {exp_lines[shorter]}"
    )


def run_golden_tests() -> list[str]:
    """Compile every case and diff against golden files. Returns failure descriptions."""
    failures: list[str] = []
    compiled: list[str] = []

    def _check(label: str, source: Path, golden: Path,
               extra_flags: list[str] | None = None) -> None:
        tmp = BUILD_DIR / golden.name
        try:
            generated = compile_to_asm(source, tmp, extra_flags)
            _diff_golden(label, generated, golden)
            compiled.append(label)
        except TestFailure as exc:
            failures.append(str(exc))

    for case in CASES:
        _check(case.source, CASES_DIR / case.source,
               GOLDEN_DIR / Path(case.source).with_suffix(".asm").name)

    for case in BEG_CASES:
        _check(f"[beginner] {case.source}", CASES_DIR / case.source,
               GOLDEN_DIR / Path(case.source).with_suffix(".asm").name,
               extra_flags=["--beginner-style"])

    for label in compiled:
        print(f"  GOLDEN OK  {label}")
    return failures


def compile_case(case: Case, extra_flags: list[str] | None = None) -> tuple[Path, Path]:
    source = CASES_DIR / case.source
    asm = BUILD_DIR / source.with_suffix(".asm").name
    obj = BUILD_DIR / source.with_suffix(".obj").name

    cmd = COMPILER_CMD + [str(source), "-o", str(asm)]
    if extra_flags:
        cmd.extend(extra_flags)
    run(cmd, cwd=ROOT)
    run([str(LC3AS), str(asm.with_suffix(""))], cwd=LC3TOOLS_DIR)

    generated_obj = asm.with_suffix(".obj")
    generated_sym = asm.with_suffix(".sym")
    shutil.move(generated_obj, obj)
    shutil.move(generated_sym, BUILD_DIR / generated_sym.name)
    return asm, obj


def verify_debug_comments() -> None:
    source = CASES_DIR / "for_and_call.c"
    asm = BUILD_DIR / "for_and_call.debug.asm"
    run(COMPILER_CMD + [str(source), "-o", str(asm), "-d"], cwd=ROOT)
    text = asm.read_text(encoding="utf-8")
    required = [
        "; int sum_to(int n)",
        "; stack frame layout",
        "; for (i = 0; i < n; i = i + 1)",
        "; add(acc, i)",
    ]
    for marker in required:
        if marker not in text:
            raise TestFailure(f"debug assembly missing marker {marker!r}\n{text}")


def verify_beginner_style_success() -> None:
    source = CASES_DIR / "puts_putchar.c"
    asm = BUILD_DIR / "puts_putchar.beginner.asm"
    obj = BUILD_DIR / "puts_putchar.beginner.obj"
    run(COMPILER_CMD + [str(source), "-o", str(asm), "--beginner-style"], cwd=ROOT)
    run([str(LC3AS), str(asm.with_suffix(""))], cwd=LC3TOOLS_DIR)

    generated_obj = asm.with_suffix(".obj")
    generated_sym = asm.with_suffix(".sym")
    shutil.move(generated_obj, obj)
    shutil.move(generated_sym, BUILD_DIR / generated_sym.name)

    output = simulate(obj, commands="file " + str(obj) + "\ncontinue\nquit\n")
    ensure_output_contains(output, "OK\nA\n")


def verify_beginner_style_stack_case_runs() -> None:
    source = CASES_DIR / "for_and_call_output.c"
    asm = BUILD_DIR / "for_and_call_output.beginner.asm"
    obj = BUILD_DIR / "for_and_call_output.beginner.obj"
    run(COMPILER_CMD + [str(source), "-o", str(asm), "--beginner-style"], cwd=ROOT)
    text = asm.read_text(encoding="utf-8")
    if not text.startswith(".ORIG x3000\nmain\n"):
        raise TestFailure(f"beginner-style output should start directly at main:\n{text}")
    # Quick reference checks for stack/frame-pointer patterns.
    # These are NOT absolute rules — they flag code that *looks* like a
    # compiler-generated calling convention.  If a check fires, inspect
    # the actual LC-3 code to decide.
    notes = []
    if "STACK_TOP" in text:
        notes.append("has STACK_TOP")
    if "LD R6," in text:
        notes.append("has 'LD R6, ...' (possible stack init)")
    if "ADD R5, R6, #0" in text:
        notes.append("has 'ADD R5, R6, #0' (possible frame-pointer setup)")
    if "STR R5, R6, #0" in text:
        notes.append("has 'STR R5, R6, #0' (possible frame save)")
    if "STR R7, R6, #0" in text:
        notes.append("has 'STR R7, R6, #0' (possible R7 stack save)")
    if "ADD R6, R6, #-1" in text or "ADD R6, R6, #1" in text:
        notes.append("has stack push/pop (ADD R6, R6, #±1)")
    if notes:
        print(f"[note] beginner-style reference check for {source.name}:")
        for n in notes:
            print(f"       {n}")
        print(f"       (inspect the .asm to verify — may be a false positive)")

    run([str(LC3AS), str(asm.with_suffix(""))], cwd=LC3TOOLS_DIR)
    generated_obj = asm.with_suffix(".obj")
    generated_sym = asm.with_suffix(".sym")
    shutil.move(generated_obj, obj)
    shutil.move(generated_sym, BUILD_DIR / generated_sym.name)

    output = simulate(obj, commands="file " + str(obj) + "\ncontinue\nquit\n")
    ensure_output_contains(output, "6\n")


def _simulate_tty(obj: Path, *, commands: str, timeout: int = 20) -> str:
    """Run lc3sim on a real pty so GETC receives program input reliably."""
    marker = "\ncontinue\n"
    if marker not in commands:
        raise TestFailure(f"tty simulation command missing continue marker:\n{commands}")
    file_command, program_tail = commands.split(marker, 1)
    quit_command = ""
    if program_tail.endswith("quit\n"):
        program_input = program_tail[: -len("quit\n")]
        quit_command = "quit\n"
    else:
        program_input = program_tail

    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(LC3TOOLS_DIR)
        os.execv("./lc3sim", ["./lc3sim"])

    output: list[str] = []
    deadline = time.monotonic() + timeout

    def _read_available(wait: float = 0.05) -> None:
        while True:
            ready, _, _ = select.select([fd], [], [], wait)
            if not ready:
                return
            try:
                data = os.read(fd, 4096)
            except OSError:
                return
            if not data:
                return
            output.append(data.decode("utf-8", errors="replace"))
            wait = 0

    def _wait_for(text: str, start: int = 0) -> None:
        while text not in "".join(output)[start:]:
            if time.monotonic() > deadline:
                raise subprocess.TimeoutExpired("lc3sim pty", timeout, output="".join(output))
            _read_available(0.1)
            done, _ = os.waitpid(pid, os.WNOHANG)
            if done:
                return

    def _write(text: str) -> None:
        os.write(fd, text.encode("utf-8"))

    try:
        _wait_for("(lc3sim)")
        _write("option flush off\n")
        _wait_for("Will not flush")
        _write(file_command + "\n")
        _wait_for("set PC")
        after_load = len("".join(output))
        _write("continue\n")
        time.sleep(0.1)
        _read_available(0)
        for ch in program_input:
            _write(ch)
            time.sleep(0.1)
            _read_available(0)
        _wait_for("(lc3sim)", after_load)
        if quit_command:
            _write(quit_command)

        while True:
            if time.monotonic() > deadline:
                raise subprocess.TimeoutExpired("lc3sim pty", timeout, output="".join(output))
            _read_available(0.1)
            done, status = os.waitpid(pid, os.WNOHANG)
            if done:
                break
        return "".join(output)
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            done, _ = os.waitpid(pid, os.WNOHANG)
            if not done:
                os.kill(pid, 15)
                os.waitpid(pid, 0)
        except (ChildProcessError, ProcessLookupError):
            pass


def simulate(obj: Path, *, commands: str, needs_tty: bool = False) -> str:
    if needs_tty:
        return _simulate_tty(obj, commands=commands)
    return run([str(LC3SIM)], cwd=LC3TOOLS_DIR, input_text=commands)


def extract_global_value(output: str) -> int:
    matches = re.findall(r"Address x[0-9A-Fa-f]+ has value x([0-9A-Fa-f]{4})\.", output)
    if not matches:
        raise TestFailure(f"could not find translated global value in simulator output:\n{output}")
    return int(matches[-1], 16)


def ensure_output_contains(output: str, expected: str) -> None:
    normalized_output = output.replace("\r\n", "\n").replace("\r", "\n")
    normalized_expected = expected.replace("\r\n", "\n").replace("\r", "\n")
    if normalized_expected not in normalized_output:
        raise TestFailure(f"expected program output {expected!r} not found in simulator output:\n{output}")


def _gcc_source(source: Path, case: Case) -> str:
    text = source.read_text(encoding="utf-8")
    prefix = (
        "#include <stdbool.h>\n"
        "#include <stdint.h>\n"
        "#include <stdio.h>\n"
        "static int lc3_getchar(void) { return fgetc(stdin); }\n"
        "static int lc3_putchar(int ch) { fputc((unsigned char)ch, stdout); return 0; }\n"
        "static int lc3_puts(const char *s) { fputs(s, stdout); return 0; }\n"
        "#define getchar lc3_getchar\n"
        "#define putchar lc3_putchar\n"
        "#define puts lc3_puts\n"
    )
    if case.expected_global is None:
        return prefix + text

    global_name = case.expected_global[0]
    return (
        prefix
        + "#define main lc3_user_main\n"
        + text
        + "\n#undef main\n"
        + "int main(void) {\n"
        + "    int rc = lc3_user_main();\n"
        + f"    printf(\"__GLOBAL__:%u\\n\", (unsigned)((uint16_t){global_name}));\n"
        + "    return rc;\n"
        + "}\n"
    )


def run_gcc_case(case: Case) -> None:
    if shutil.which("gcc") is None:
        raise TestFailure("gcc not found; local full test requires gcc for oracle comparison")

    source = CASES_DIR / case.source
    with tempfile.TemporaryDirectory(prefix="compiler-lc3-gcc-") as tmpdir:
        tmp = Path(tmpdir)
        wrapped = tmp / source.name
        elf = tmp / "program.elf"
        wrapped.write_text(_gcc_source(source, case), encoding="utf-8")
        run(["gcc", "-std=c11", "-w", "-o", str(elf), str(wrapped)], cwd=ROOT)
        stdout = run([str(elf)], cwd=ROOT, input_text=case.program_input)

    if case.expected_output is not None:
        expected = case.expected_output.replace("\r\n", "\n").replace("\r", "\n")
        actual = stdout.replace("\r\n", "\n").replace("\r", "\n")
        if actual != expected:
            raise TestFailure(f"{case.source}: gcc output differs from expected\n  expected: {expected!r}\n  got:      {actual!r}")

    if case.expected_global is not None:
        match = re.search(r"__GLOBAL__:(\d+)", stdout)
        if not match:
            raise TestFailure(f"{case.source}: gcc oracle did not print global marker:\n{stdout}")
        actual = int(match.group(1))
        expected = case.expected_global[1] & 0xFFFF
        if actual != expected:
            raise TestFailure(
                f"{case.source}: gcc expected {case.expected_global[0]} = x{expected:04X}, got x{actual:04X}\n{stdout}"
            )


def main() -> int:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    def _progress(msg: str) -> None:
        print(f"[test] {msg}", flush=True)

    # ── 1. Golden comparison (always) ──
    print("=== golden file comparison ===", flush=True)
    golden_failures = run_golden_tests()
    if golden_failures:
        for f in golden_failures:
            print(f"FAIL {f}")
        print(f"\n{golden_failures.__len__()} GOLDEN MISMATCH(ES)")
        return 1

    if IS_CI:
        print(f"\nCI mode: {len(CASES) + len(BEG_CASES)} golden files match. Done.")
        return 0

    # ── 2. Local-only: full simulation ──
    print("\n=== local simulation ===", flush=True)

    _progress("verify debug comments...")
    verify_debug_comments()
    _progress("verify beginner style...")
    verify_beginner_style_success()
    _progress("verify beginner stack case...")
    verify_beginner_style_stack_case_runs()

    failures: list[str] = []
    for case in CASES:
        try:
            _progress(case.source)
            _, obj = compile_case(case)
            commands = f"file {obj}\ncontinue\n"
            if case.expected_global is not None:
                commands += f"translate G_{case.expected_global[0]}\n"
            commands += case.program_input
            commands += "quit\n"
            output = simulate(obj, commands=commands, needs_tty=bool(case.program_input))

            if case.expected_global is not None:
                value = extract_global_value(output)
                expected = case.expected_global[1] & 0xFFFF
                if value != expected:
                    raise TestFailure(
                        f"{case.source}: expected G_{case.expected_global[0]} = x{expected:04X}, got x{value:04X}\n{output}"
                    )
            if case.expected_output is not None:
                ensure_output_contains(output, case.expected_output)
        except subprocess.TimeoutExpired as exc:
            failures.append(f"{case.source}: timeout after {exc.timeout}s\n{exc}")
        except Exception as exc:
            failures.append(str(exc))

    for case in BEG_CASES:
        try:
            _progress(f"[beginner] {case.source}")
            _, obj = compile_case(case, extra_flags=["--beginner-style"])
            commands = f"file {obj}\ncontinue\n"
            commands += case.program_input
            commands += "quit\n"
            output = simulate(obj, commands=commands, needs_tty=bool(case.program_input))
            if case.expected_output is not None:
                ensure_output_contains(output, case.expected_output)
        except subprocess.TimeoutExpired as exc:
            failures.append(f"[beginner] {case.source}: timeout after {exc.timeout}s\n{exc}")
        except Exception as exc:
            failures.append(f"[beginner] {case.source}: {exc}")

    if failures:
        for failure in failures:
            print(failure)
            print("-" * 80)
        print(f"\n{failures.__len__()} SIMULATION FAILURE(S)")
        return 1

    print("\n=== gcc oracle comparison ===", flush=True)
    gcc_failures: list[str] = []
    for case in CASES + BEG_CASES:
        try:
            _progress(f"[gcc] {case.source}")
            run_gcc_case(case)
        except subprocess.TimeoutExpired as exc:
            gcc_failures.append(f"{case.source}: gcc timeout after {exc.timeout}s\n{exc}")
        except Exception as exc:
            gcc_failures.append(str(exc))

    if gcc_failures:
        for failure in gcc_failures:
            print(failure)
            print("-" * 80)
        print(f"\n{gcc_failures.__len__()} GCC ORACLE FAILURE(S)")
        return 1

    print(f"\nALL {len(CASES) + len(BEG_CASES)} TESTS PASSED (golden + simulation + gcc oracle)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
