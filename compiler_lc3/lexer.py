from __future__ import annotations

from dataclasses import dataclass


KEYWORDS = {
    "int",
    "if",
    "else",
    "while",
    "for",
    "break",
    "continue",
    "return",
}

TWO_CHAR = {"<=", ">=", "==", "!=", "&&", "||", "++", "--"}
SINGLE_CHAR = set("(){};,=+-!<>")


@dataclass
class Token:
    kind: str
    value: str
    line: int
    column: int


class LexerError(ValueError):
    pass


class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source
        self.length = len(source)
        self.index = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while not self._eof():
            ch = self._peek()
            if ch in " \t\r":
                self._advance()
                continue
            if ch == "\n":
                self._advance_line()
                continue
            if ch == "/" and self._peek(1) == "/":
                self._skip_line_comment()
                continue
            if ch == "/" and self._peek(1) == "*":
                self._skip_block_comment()
                continue
            if ch.isalpha() or ch == "_":
                tokens.append(self._identifier())
                continue
            if ch.isdigit():
                tokens.append(self._number())
                continue
            if ch == '"':
                tokens.append(self._string())
                continue

            start_line, start_col = self.line, self.column
            pair = ch + self._peek(1)
            if pair in TWO_CHAR:
                self._advance()
                self._advance()
                tokens.append(Token(pair, pair, start_line, start_col))
                continue
            if ch in SINGLE_CHAR:
                self._advance()
                tokens.append(Token(ch, ch, start_line, start_col))
                continue
            raise LexerError(f"unexpected character {ch!r} at {start_line}:{start_col}")

        tokens.append(Token("EOF", "", self.line, self.column))
        return tokens

    def _identifier(self) -> Token:
        start = self.index
        line, col = self.line, self.column
        while not self._eof() and (self._peek().isalnum() or self._peek() == "_"):
            self._advance()
        text = self.source[start:self.index]
        kind = text if text in KEYWORDS else "IDENT"
        return Token(kind, text, line, col)

    def _number(self) -> Token:
        start = self.index
        line, col = self.line, self.column
        while not self._eof() and self._peek().isdigit():
            self._advance()
        return Token("NUMBER", self.source[start:self.index], line, col)

    def _string(self) -> Token:
        line, col = self.line, self.column
        self._advance()
        chars: list[str] = []
        while not self._eof() and self._peek() != '"':
            ch = self._peek()
            if ch == "\\":
                self._advance()
                if self._eof():
                    raise LexerError(f"unterminated string at {line}:{col}")
                esc = self._peek()
                mapping = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
                if esc not in mapping:
                    raise LexerError(f"unsupported escape \\{esc} at {self.line}:{self.column}")
                chars.append(mapping[esc])
                self._advance()
                continue
            if ch == "\n":
                raise LexerError(f"newline in string literal at {self.line}:{self.column}")
            chars.append(ch)
            self._advance()
        if self._eof():
            raise LexerError(f"unterminated string at {line}:{col}")
        self._advance()
        return Token("STRING", "".join(chars), line, col)

    def _skip_line_comment(self) -> None:
        while not self._eof() and self._peek() != "\n":
            self._advance()

    def _skip_block_comment(self) -> None:
        self._advance()
        self._advance()
        while not self._eof():
            if self._peek() == "*" and self._peek(1) == "/":
                self._advance()
                self._advance()
                return
            if self._peek() == "\n":
                self._advance_line()
            else:
                self._advance()
        raise LexerError("unterminated block comment")

    def _peek(self, offset: int = 0) -> str:
        idx = self.index + offset
        if idx >= self.length:
            return "\0"
        return self.source[idx]

    def _advance(self) -> None:
        self.index += 1
        self.column += 1

    def _advance_line(self) -> None:
        self.index += 1
        self.line += 1
        self.column = 1

    def _eof(self) -> bool:
        return self.index >= self.length
