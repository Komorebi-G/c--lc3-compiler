#!/usr/bin/env python3
"""Run a C test case through both gcc and compiler-lc3, compare results.

Usage: python3 tests/oracle.py tests/cases/multiply.c
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LC3TOOLS = ROOT / "lc3tools"
COMPILER_CMD = [sys.executable, "-m", "compiler_lc3"]


def run_gcc_oracle(source: Path) -> tuple[int, str]:
    """Compile with gcc, run, return (exit_code, stdout)."""
    with tempfile.NamedTemporaryFile(suffix=".elf", delete=False) as tmp:
        elf = Path(tmp.name)
    try:
        subprocess.run(["gcc", "-w", "-o", str(elf), str(source)],
                       capture_output=True, check=True)
        r = subprocess.run([str(elf)], capture_output=True, text=True, timeout=5)
        return r.returncode, r.stdout
    finally:
        elf.unlink(missing_ok=True)


def run_lc3_oracle(source: Path) -> tuple[int, str]:
    """Compile with compiler-lc3, assemble, simulate, return (exit_code, stdout)."""
    build = ROOT / "tests" / "build"
    build.mkdir(parents=True, exist_ok=True)
    asm = build / source.with_suffix(".asm").name
    obj = build / source.with_suffix(".obj").name

    # Compile
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    subprocess.run(COMPILER_CMD + [str(source), "-o", str(asm)],
                   cwd=ROOT, env=env, capture_output=True, check=True)

    # Assemble
    subprocess.run([str(LC3TOOLS / "lc3as"), str(asm.with_suffix(""))],
                   cwd=LC3TOOLS, capture_output=True, check=True)
    # lc3as puts .obj next to .asm by default
    gen_obj = asm.with_suffix(".obj")
    gen_sym = asm.with_suffix(".sym")
    if gen_obj.exists():
        shutil.move(str(gen_obj), str(obj))
    if gen_sym.exists():
        shutil.move(str(gen_sym), str(build / gen_sym.name))

    # Simulate via bash pipe (subprocess.run(input=...) deadlocks with lc3sim)
    cmds = f"file {obj}\\ncontinue\\nquit\\n"
    r = subprocess.run(
        ["bash", "-c", f'echo -e "{cmds}" | timeout 10 {LC3TOOLS}/lc3sim'],
        capture_output=True, text=True, timeout=15,
    )
    out = r.stdout + r.stderr
    # Extract program output.  lc3sim prints:
    #   (lc3sim) Loaded "..." and set PC to x3000
    #   (lc3sim) <program output>
    # The output is on the same line as the final "(lc3sim) " prompt.
    import re
    m = re.search(r"set PC to x[0-9A-Fa-f]+.*?\n\(lc3sim\)\s*(.*)", out, re.DOTALL)
    if m:
        output = m.group(1).rstrip()
        if output:
            return 0, output + "\n"
    # Fallback: try matching output that appears before a prompt
    m = re.search(r"set PC to x[0-9A-Fa-f]+.*?\n(.*)", out, re.DOTALL)
    if m:
        tail = m.group(1)
        for line in tail.splitlines():
            s = line.strip()
            if s.startswith("(lc3sim)"):
                body = s[8:].strip()  # strip "(lc3sim)" prefix
                if body:
                    return 0, body + "\n"
    return 0, ""


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 tests/oracle.py <test.c>", file=sys.stderr)
        return 1

    source = Path(sys.argv[1]).resolve()
    if not source.exists():
        print(f"File not found: {source}", file=sys.stderr)
        return 1

    print(f"Testing: {source.name}")
    print(f"  Source: {source}")

    # GCC oracle
    gcc_rc, gcc_out = run_gcc_oracle(source)
    print(f"  gcc:     rc={gcc_rc} out={gcc_out!r}")

    # LC-3 oracle
    try:
        lc3_rc, lc3_out = run_lc3_oracle(source)
        print(f"  compiler-lc3: rc={lc3_rc} out={lc3_out!r}")
    except subprocess.CalledProcessError as e:
        print(f"  compiler-lc3 FAILED: {e.stderr}")
        return 1

    if gcc_out == lc3_out:
        print("  PASS (output matches gcc)")
        return 0

    print("  FAIL: output differs from gcc")
    print(f"  gcc:     {gcc_out!r}")
    print(f"  lc3:     {lc3_out!r}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
