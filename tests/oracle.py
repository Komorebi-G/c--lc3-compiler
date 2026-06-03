#!/usr/bin/env python3
"""Run registered test cases through the gcc oracle.

The main regression runner compares observed LC-3 simulation results directly
against observed gcc results.  This helper is useful when you only want to
check the native C side.

Usage:
    python3 tests/oracle.py
    python3 tests/oracle.py tests/cases/array_loop.c
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.run_tests import BEG_CASES, CASES, CASES_DIR, Case, run_gcc_case


def _registered_cases() -> list[Case]:
    return CASES + BEG_CASES


def _find_case(path_or_name: str) -> Case | None:
    name = Path(path_or_name).name
    for case in _registered_cases():
        if case.source == name:
            return case
    return None


def main() -> int:
    if len(sys.argv) > 2:
        print("Usage: python3 tests/oracle.py [tests/cases/name.c]", file=sys.stderr)
        return 1

    if len(sys.argv) == 2:
        case = _find_case(sys.argv[1])
        if case is None:
            print(f"Case is not registered in tests/run_tests.py: {sys.argv[1]}", file=sys.stderr)
            return 1
        cases = [case]
    else:
        cases = _registered_cases()

    for case in cases:
        run_gcc_case(case)
        print(f"GCC OK  {CASES_DIR / case.source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
