from __future__ import annotations

from . import ast
from .lexer import Token


class ParserError(ValueError):
    pass


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.index = 0

    def _parse_type_spec(self) -> ast.Type:
        """Parse a type specifier: int, char, bool."""
        if self._check("int") or self._check("char") or self._check("bool"):
            base = self._advance().kind
            return ast.Type(base, 0)
        raise self._error(f"expected type, found {self._peek().kind}")

    def _parse_declarator(self, base_type: ast.Type) -> tuple[str, ast.Type]:
        """Parse a declarator: optional *s, then IDENT. Returns (name, full_type)."""
        ptr_depth = 0
        while self._match("*"):
            ptr_depth += 1
        name = self._expect("IDENT").value
        return name, ast.Type(base_type.base, base_type.ptr_depth + ptr_depth)

    def parse_program(self) -> ast.Program:
        globals_: list[ast.GlobalDecl] = []
        functions: list[ast.FunctionDef] = []
        while not self._check("EOF"):
            base = self._parse_type_spec()
            # Pointer declarator for function return type? e.g. int* func() — skip *s
            ptr_depth = 0
            while self._match("*"):
                ptr_depth += 1
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
            self._parse_type_spec()
            # Skip pointer *s in param decl
            while self._match("*"):
                pass
            params.append(self._expect("IDENT").value)
            if self._match(")"):
                return params
            self._expect(",")

    def _parse_block(self) -> ast.Block:
        self._expect("{")
        items: list[ast.BlockItem] = []
        while not self._check("}"):
            if self._check("int") or self._check("char") or self._check("bool"):
                items.append(self._parse_decl())
            else:
                items.append(self._parse_stmt())
        self._expect("}")
        return ast.Block(items)

    def _parse_decl(self) -> ast.BlockItem:
        base_type = self._parse_type_spec()
        name, var_type = self._parse_declarator(base_type)
        # Array declaration: int arr[size];
        if self._match("["):
            size = int(self._expect("NUMBER").value)
            self._expect("]")
            init_list = None
            if self._match("="):
                self._expect("{")
                init_list = []
                while not self._check("}"):
                    init_list.append(self._parse_expr())
                    if not self._match(","):
                        break
                self._expect("}")
            self._expect(";")
            return ast.ArrayDecl(name, size, init_list)
        # Scalar declaration
        init = None
        if self._match("="):
            init = self._parse_expr()
        self._expect(";")
        return ast.VarDecl(name, init, var_type)

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

    # Compound assignment operators and their underlying binary ops.
    _COMPOUND = {"+=": "+", "-=": "-", "*=": "*", "/=": "/", "%=": "%"}

    def _parse_assignment(self) -> ast.Expr:
        expr = self._parse_logical_or()

        # Detect = or compound assignment (+=, -=, *=, /=, %=)
        op = None
        if self._check("="):
            op = "="
        else:
            for cop in self._COMPOUND:
                if self._check(cop):
                    op = cop
                    break
        if op is None:
            return expr

        self._advance()  # consume the assignment operator
        rhs = self._parse_assignment()

        # Simple assignment: x = rhs
        if op == "=":
            if isinstance(expr, ast.Variable):
                return ast.Assign(expr.name, rhs)
            if isinstance(expr, ast.ArrayAccess) and isinstance(expr.array, ast.Variable):
                return ast.ArrayAssign(expr.array.name, expr.index, rhs)
            if isinstance(expr, ast.Deref):
                return ast.DerefAssign(expr.operand, rhs)
            raise self._error("left side of assignment must be a variable, array element, or *ptr")

        # Compound assignment: desugar lvalue op= rhs  →  lvalue = lvalue op rhs
        binop = self._COMPOUND[op]

        # Build a copy of the lvalue for use in the binary op.
        if isinstance(expr, ast.Variable):
            lhs_copy: ast.Expr = ast.Variable(expr.name)
        elif isinstance(expr, ast.ArrayAccess) and isinstance(expr.array, ast.Variable):
            lhs_copy = ast.ArrayAccess(ast.Variable(expr.array.name), expr.index)
        elif isinstance(expr, ast.Deref):
            lhs_copy = ast.Deref(expr.operand)
        else:
            raise self._error("left side of assignment must be a variable, array element, or *ptr")

        combined = ast.BinaryOp(binop, lhs_copy, rhs)

        if isinstance(expr, ast.Variable):
            return ast.Assign(expr.name, combined)
        if isinstance(expr, ast.ArrayAccess) and isinstance(expr.array, ast.Variable):
            return ast.ArrayAssign(expr.array.name, expr.index, combined)
        # ast.Deref
        return ast.DerefAssign(expr.operand, combined)

    def _parse_logical_or(self) -> ast.Expr:
        expr = self._parse_logical_and()
        while self._check("||"):
            op = self._advance().kind
            rhs = self._parse_logical_and()
            expr = ast.BinaryOp(op, expr, rhs)
        return expr

    def _parse_logical_and(self) -> ast.Expr:
        expr = self._parse_equality()
        while self._check("&&"):
            op = self._advance().kind
            rhs = self._parse_equality()
            expr = ast.BinaryOp(op, expr, rhs)
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

    def _parse_multiplicative(self) -> ast.Expr:
        expr = self._parse_unary()
        while self._check("*") or self._check("/") or self._check("%"):
            op = self._advance().kind
            rhs = self._parse_unary()
            expr = ast.BinaryOp(op, expr, rhs)
        return expr

    def _parse_additive(self) -> ast.Expr:
        expr = self._parse_multiplicative()
        while self._check("+") or self._check("-"):
            op = self._advance().kind
            rhs = self._parse_multiplicative()
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
        if self._match("*"):
            return ast.Deref(self._parse_unary())
        if self._match("&"):
            operand = self._parse_unary()
            if not isinstance(operand, (ast.Variable, ast.ArrayAccess)):
                raise self._error("operand of & must be a variable or array element")
            return ast.AddrOf(operand)
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
            if self._match("["):
                index = self._parse_expr()
                self._expect("]")
                expr = ast.ArrayAccess(expr, index)
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
