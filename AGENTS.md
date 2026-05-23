# Repository Guidelines

## Project Structure & Module Organization

`compiler_lc3/` contains the compiler pipeline: `lexer.py`, `parser.py`, `ast.py`, `optimizer.py`, `codegen.py`, and the CLI entry in `__main__.py`. Put new compiler stages or helpers here rather than in `tests/`.

`tests/cases/` holds end-to-end C input programs. `tests/run_tests.py` compiles each case, assembles it with `lc3tools/`, and checks simulator output. `examples/` contains sample programs, while `build/` and `tests/build/` are generated output directories. `lc3tools/` is a bundled upstream toolchain; avoid unrelated style cleanups there.

## Build, Test, and Development Commands

Compile a source file:

```bash
python3 -m compiler_lc3 examples/sum.c -o build/sum.asm
```

Generate assembly with source-oriented debug comments:

```bash
python3 -m compiler_lc3 tests/cases/for_and_call.c -o tests/build/for_and_call.asm -d
```

Build the bundled LC-3 tools when needed:

```bash
cd lc3tools
./configure --installdir "$PWD/install"
make && make install
```

Run the regression suite:

```bash
python3 tests/run_tests.py
```

## Coding Style & Naming Conventions

Use Python 3 with 4-space indentation, type hints, and small focused classes/functions. Follow the existing style: `snake_case` for functions and variables, `CapWords` for classes, and explicit dataclasses for structured records such as tokens or test cases.

Keep parser and codegen logic straightforward and local; prefer clear helper methods over clever abstractions. Preserve the current direct error-reporting style with line/column details.

## Testing Guidelines

Add new language coverage by placing a `.c` case in `tests/cases/` and registering it in `CASES` inside `tests/run_tests.py`. Name tests after the feature under test, for example `while_break_continue.c` or `puts_putchar.c`.

Generated LC-3 must be verified by actual tools, not just by successful code generation. For compiler changes, run `python3 tests/run_tests.py`, which compiles cases, assembles them with `lc3as`, and runs them in `lc3sim` to check globals, input, and output.

If a change affects code generation modes or flags, verify each affected variant can run. At minimum, check default output, `-d`, and any mode-specific flags such as `--beginner-style`; unsupported combinations must fail explicitly rather than emit broken assembly.

Changes that affect emitted comments should also pass the debug-comment assertions in `verify_debug_comments()`.

## Commit & Pull Request Guidelines

This repository currently has no recorded commit history, so use short imperative commit subjects such as `parser: support unary minus in for clauses`. Keep commits scoped to one behavior change.

Pull requests should summarize the language feature or fix, list affected modules, and include the exact verification command you ran. When output changes, include a short assembly or simulator excerpt in the PR description.
