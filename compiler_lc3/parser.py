from __future__ import annotations

from . import ast
from .lexer import Token


class ParserError(ValueError):
    pass


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.index = 0

    def parse_program(self) -> ast.Program:
        globals_: list[ast.GlobalDecl] = []
        functions: list[ast.FunctionDef] = []
        while not self._check("EOF"):
            self._expect("int")
            name = self._expect("IDENT").value
            if self._match("("):
                params = self._parse_params()
                body = self._parse_block()
                functions.append(ast.FunctionDef(name, params, body))
            else:
                init = None
                if self._match("="):
                    init = int(self._expect("NUMBER").value)
                self._expect(";")
                globals_.append(ast.GlobalDecl(name, init))
        return ast.Program(globals_, functions)

    def _parse_params(self) -> list[str]:
        params: list[str] = []
        if self._match(")"):
            return params
        while True:
            self._expect("int")
            params.append(self._expect("IDENT").value)
            if self._match(")"):
                return params
            self._expect(",")

    def _parse_block(self) -> ast.Block:
        self._expect("{")
        items: list[ast.BlockItem] = []
        while not self._check("}"):
            if self._check("int"):
                items.append(self._parse_decl())
            else:
                items.append(self._parse_stmt())
        self._expect("}")
        return ast.Block(items)

    def _parse_decl(self) -> ast.VarDecl:
        self._expect("int")
        name = self._expect("IDENT").value
        init = None
        if self._match("="):
            init = self._parse_expr()
        self._expect(";")
        return ast.VarDecl(name, init)

    def _parse_stmt(self) -> ast.Statement:
        if self._match("{"):
            self.index -= 1
            return ast.BlockStmt(self._parse_block())
        if self._match("if"):
            self._expect("(")
            cond = self._parse_expr()
            self._expect(")")
            then_branch = self._parse_stmt()
            else_branch = None
            if self._match("else"):
                else_branch = self._parse_stmt()
            return ast.IfStmt(cond, then_branch, else_branch)
        if self._match("while"):
            self._expect("(")
            cond = self._parse_expr()
            self._expect(")")
            return ast.WhileStmt(cond, self._parse_stmt())
        if self._match("for"):
            self._expect("(")
            init = None if self._check(";") else self._parse_expr()
            self._expect(";")
            cond = None if self._check(";") else self._parse_expr()
            self._expect(";")
            step = None if self._check(")") else self._parse_expr()
            self._expect(")")
            return ast.ForStmt(init, cond, step, self._parse_stmt())
        if self._match("break"):
            self._expect(";")
            return ast.BreakStmt()
        if self._match("continue"):
            self._expect(";")
            return ast.ContinueStmt()
        if self._match("return"):
            expr = None if self._check(";") else self._parse_expr()
            self._expect(";")
            return ast.ReturnStmt(expr)
        expr = self._parse_expr()
        self._expect(";")
        return ast.ExprStmt(expr)

    def _parse_expr(self) -> ast.Expr:
        return self._parse_assignment()

    def _parse_assignment(self) -> ast.Expr:
        expr = self._parse_equality()
        if self._match("="):
            if not isinstance(expr, ast.Variable):
                raise self._error("left side of assignment must be a variable")
            return ast.Assign(expr.name, self._parse_assignment())
        return expr

    def _parse_equality(self) -> ast.Expr:
        expr = self._parse_relational()
        while self._check("==") or self._check("!="):
            op = self._advance().kind
            rhs = self._parse_relational()
            expr = ast.BinaryOp(op, expr, rhs)
        return expr

    def _parse_relational(self) -> ast.Expr:
        expr = self._parse_additive()
        while self._check("<") or self._check("<=") or self._check(">") or self._check(">="):
            op = self._advance().kind
            rhs = self._parse_additive()
            expr = ast.BinaryOp(op, expr, rhs)
        return expr

    def _parse_additive(self) -> ast.Expr:
        expr = self._parse_unary()
        while self._check("+") or self._check("-"):
            op = self._advance().kind
            rhs = self._parse_unary()
            expr = ast.BinaryOp(op, expr, rhs)
        return expr

    def _parse_unary(self) -> ast.Expr:
        if self._match("++"):
            operand = self._parse_unary()
            if not isinstance(operand, ast.Variable):
                raise self._error("operand of prefix ++ must be a variable")
            return ast.IncDecOp(operand.name, 1, False)
        if self._match("--"):
            operand = self._parse_unary()
            if not isinstance(operand, ast.Variable):
                raise self._error("operand of prefix -- must be a variable")
            return ast.IncDecOp(operand.name, -1, False)
        if self._match("-"):
            return ast.UnaryOp("-", self._parse_unary())
        if self._match("!"):
            return ast.UnaryOp("!", self._parse_unary())
        return self._parse_primary()

    def _parse_primary(self) -> ast.Expr:
        if self._match("NUMBER"):
            return ast.IntLiteral(int(self._previous().value))
        if self._match("STRING"):
            return ast.StringLiteral(self._previous().value)
        if self._match("IDENT"):
            name = self._previous().value
            if self._match("("):
                args: list[ast.Expr] = []
                if not self._check(")"):
                    while True:
                        args.append(self._parse_expr())
                        if self._match(")"):
                            break
                        self._expect(",")
                else:
                    self._expect(")")
                return ast.Call(name, args)
            expr: ast.Expr = ast.Variable(name)
            if self._match("++"):
                return ast.IncDecOp(name, 1, True)
            if self._match("--"):
                return ast.IncDecOp(name, -1, True)
            return expr
        if self._match("("):
            expr = self._parse_expr()
            self._expect(")")
            return expr
        raise self._error(f"unexpected token {self._peek().kind}")

    def _match(self, kind: str) -> bool:
        if self._check(kind):
            self._advance()
            return True
        return False

    def _check(self, kind: str) -> bool:
        return self._peek().kind == kind

    def _advance(self) -> Token:
        token = self.tokens[self.index]
        self.index += 1
        return token

    def _previous(self) -> Token:
        return self.tokens[self.index - 1]

    def _peek(self) -> Token:
        return self.tokens[self.index]

    def _expect(self, kind: str) -> Token:
        if not self._check(kind):
            raise self._error(f"expected {kind}, found {self._peek().kind}")
        return self._advance()

    def _error(self, message: str) -> ParserError:
        token = self._peek()
        return ParserError(f"{message} at {token.line}:{token.column}")
