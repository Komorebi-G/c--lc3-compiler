from __future__ import annotations

import argparse
from pathlib import Path

from .codegen import CodeGenerator
from .lexer import Lexer
from .optimizer import optimize_program
from .parser import Parser


def compile_source(source: str, *, debug_comments: bool = False, beginner_style: bool = False) -> str:
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse_program()
    program = optimize_program(program)
    return CodeGenerator(debug_comments=debug_comments, beginner_style=beginner_style).generate(program)


def main() -> None:
    argp = argparse.ArgumentParser(description="Compile a small C subset to LC-3 assembly.")
    argp.add_argument("input", help="input C source file")
    argp.add_argument("-o", "--output", help="output LC-3 assembly file")
    argp.add_argument("-d", "--debug-comments", action="store_true", help="emit source-oriented comments into the generated assembly")
    argp.add_argument(
        "--beginner-style",
        action="store_true",
        help="emit a beginner-oriented layout, placing main directly after .ORIG instead of using a startup stub",
    )
    args = argp.parse_args()

    input_path = Path(args.input)
    source = input_path.read_text(encoding="utf-8")
    assembly = compile_source(
        source,
        debug_comments=args.debug_comments,
        beginner_style=args.beginner_style,
    )

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_suffix(".asm")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(assembly, encoding="utf-8")


if __name__ == "__main__":
    main()
