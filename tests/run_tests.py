from __future__ import annotations

import re
import shutil
import subprocess
import sys
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = ROOT / "tests" / "cases"
BUILD_DIR = ROOT / "tests" / "build"
LC3TOOLS_DIR = ROOT / "lc3tools"
COMPILER_CMD = [sys.executable, "-m", "compiler_lc3"]
LC3AS = LC3TOOLS_DIR / "lc3as"
SIM_WRAP = ["script", "-q", "-c", "./lc3sim", "/dev/null"]


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
]

BEG_CASES = [
    Case("beginner_loop_local.c", expected_output="3\n"),
    Case("beginner_nested_call.c", expected_output="5\n"),
    Case("beginner_global_local.c", expected_output="7\n"),
    Case("beginner_input_loop.c", expected_output="4\n", program_input="test\n"),
    Case("beginner_multi_func.c", expected_output="8\n"),
]


class TestFailure(RuntimeError):
    pass


def run(cmd: list[str], *, cwd: Path, input_text: str | None = None) -> str:
    env = dict(os.environ)
    env["PATH"] = f"{ROOT / '.local' / 'bin'}:{env.get('PATH', '')}"
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        input=input_text,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    if proc.returncode != 0:
        raise TestFailure(
            f"command failed: {' '.join(cmd)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc.stdout + proc.stderr


def compile_case(case: Case) -> tuple[Path, Path]:
    source = CASES_DIR / case.source
    asm = BUILD_DIR / source.with_suffix(".asm").name
    obj = BUILD_DIR / source.with_suffix(".obj").name

    run(COMPILER_CMD + [str(source), "-o", str(asm)], cwd=ROOT)
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
    if "LD R6" in text or "LDR" in text or "STR R" in text:
        raise TestFailure("beginner-style output should not use stack or LDR/STR:\n" + text)

    run([str(LC3AS), str(asm.with_suffix(""))], cwd=LC3TOOLS_DIR)
    generated_obj = asm.with_suffix(".obj")
    generated_sym = asm.with_suffix(".sym")
    shutil.move(generated_obj, obj)
    shutil.move(generated_sym, BUILD_DIR / generated_sym.name)

    output = simulate(obj, commands="file " + str(obj) + "\ncontinue\nquit\n")
    ensure_output_contains(output, "6\n")


def simulate(obj: Path, *, commands: str) -> str:
    return run(SIM_WRAP, cwd=LC3TOOLS_DIR, input_text=commands)


def extract_global_value(output: str) -> int:
    matches = re.findall(r"Address x[0-9A-Fa-f]+ has value x([0-9A-Fa-f]{4})\.", output)
    if not matches:
        raise TestFailure(f"could not find translated global value in simulator output:\n{output}")
    return int(matches[-1], 16)


def ensure_output_contains(output: str, expected: str) -> None:
    if expected not in output:
        raise TestFailure(f"expected program output {expected!r} not found in simulator output:\n{output}")


def main() -> int:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    verify_debug_comments()
    verify_beginner_style_success()
    verify_beginner_style_stack_case_runs()

    failures: list[str] = []
    for case in CASES:
        try:
            _, obj = compile_case(case)
            commands = f"file {obj}\ncontinue\n"
            if case.expected_global is not None:
                commands += f"translate G_{case.expected_global[0]}\n"
            commands += case.program_input
            commands += "quit\n"
            output = simulate(obj, commands=commands)

            if case.expected_global is not None:
                value = extract_global_value(output)
                expected = case.expected_global[1] & 0xFFFF
                if value != expected:
                    raise TestFailure(
                        f"{case.source}: expected G_{case.expected_global[0]} = x{expected:04X}, got x{value:04X}\n{output}"
                    )
            if case.expected_output is not None:
                ensure_output_contains(output, case.expected_output)
        except Exception as exc:
            failures.append(str(exc))

    for case in BEG_CASES:
        try:
            source = CASES_DIR / case.source
            asm = BUILD_DIR / source.with_suffix(".asm").name
            obj = BUILD_DIR / source.with_suffix(".obj").name
            run(COMPILER_CMD + [str(source), "-o", str(asm), "--beginner-style"], cwd=ROOT)
            run([str(LC3AS), str(asm.with_suffix(""))], cwd=LC3TOOLS_DIR)
            generated_obj = asm.with_suffix(".obj")
            generated_sym = asm.with_suffix(".sym")
            shutil.move(generated_obj, obj)
            shutil.move(generated_sym, BUILD_DIR / generated_sym.name)
            commands = f"file {obj}\ncontinue\n"
            commands += case.program_input
            commands += "quit\n"
            output = simulate(obj, commands=commands)
            if case.expected_output is not None:
                ensure_output_contains(output, case.expected_output)
        except Exception as exc:
            failures.append(f"[beginner] {case.source}: {exc}")

    if failures:
        for failure in failures:
            print(failure)
            print("-" * 80)
        return 1

    for case in CASES:
        print(f"PASS {case.source}")
    for case in BEG_CASES:
        print(f"PASS [beginner] {case.source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
