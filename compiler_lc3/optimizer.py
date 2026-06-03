from __future__ import annotations

from . import ast


COMPARE_OPS = {"<", "<=", ">", ">=", "==", "!="}


def optimize_program(program: ast.Program) -> ast.Program:
    return ast.Program(
        globals=program.globals,
        functions=[optimize_function(func) for func in program.functions],
    )


def optimize_function(func: ast.FunctionDef) -> ast.FunctionDef:
    return ast.FunctionDef(func.name, func.params, optimize_block(func.body))


def optimize_block(block: ast.Block) -> ast.Block:
    items: list[ast.BlockItem] = []
    for item in block.items:
        if isinstance(item, ast.VarDecl):
            init = optimize_expr(item.init) if item.init is not None else None
            items.append(ast.VarDecl(item.name, init, item.var_type))
        elif isinstance(item, ast.ArrayDecl):
            init_list = [optimize_expr(e) for e in item.init_list] if item.init_list else None
            items.append(ast.ArrayDecl(item.name, item.size, init_list))
        else:
            stmt = optimize_stmt(item)
            if stmt is not None:
                items.append(stmt)
    return ast.Block(items)


def optimize_stmt(stmt: ast.Statement) -> ast.Statement | None:
    if isinstance(stmt, ast.ExprStmt):
        return ast.ExprStmt(optimize_expr(stmt.expr))
    if isinstance(stmt, ast.BlockStmt):
        return ast.BlockStmt(optimize_block(stmt.block))
    if isinstance(stmt, ast.IfStmt):
        cond = optimize_expr(stmt.condition)
        then_branch = optimize_stmt(stmt.then_branch)
        else_branch = optimize_stmt(stmt.else_branch) if stmt.else_branch is not None else None
        if is_const_int(cond):
            return then_branch if const_value(cond) != 0 else else_branch
        if then_branch is None:
            then_branch = ast.BlockStmt(ast.Block([]))
        return ast.IfStmt(cond, then_branch, else_branch)
    if isinstance(stmt, ast.WhileStmt):
        cond = optimize_expr(stmt.condition)
        body = optimize_stmt(stmt.body)
        if is_const_int(cond) and const_value(cond) == 0:
            return None
        if body is None:
            body = ast.BlockStmt(ast.Block([]))
        return ast.WhileStmt(cond, body)
    if isinstance(stmt, ast.ForStmt):
        init = optimize_expr(stmt.init) if stmt.init is not None else None
        cond = optimize_expr(stmt.condition) if stmt.condition is not None else None
        step = optimize_expr(stmt.step) if stmt.step is not None else None
        body = optimize_stmt(stmt.body)
        if cond is not None and is_const_int(cond) and const_value(cond) == 0:
            if init is not None:
                return ast.ExprStmt(init)
            return None
        if body is None:
            body = ast.BlockStmt(ast.Block([]))
        return ast.ForStmt(init, cond, step, body)
    if isinstance(stmt, ast.ReturnStmt):
        expr = optimize_expr(stmt.expr) if stmt.expr is not None else None
        return ast.ReturnStmt(expr)
    return stmt


def optimize_expr(expr: ast.Expr | None) -> ast.Expr | None:
    if expr is None:
        return None
    if isinstance(expr, (ast.IntLiteral, ast.StringLiteral, ast.Variable)):
        return expr
    if isinstance(expr, ast.IncDecOp):
        return expr
    if isinstance(expr, ast.Assign):
        return ast.Assign(expr.name, optimize_expr(expr.value))
    if isinstance(expr, ast.UnaryOp):
        operand = optimize_expr(expr.operand)
        if is_const_int(operand):
            value = const_value(operand)
            if expr.op == "-":
                return ast.IntLiteral(-value)
            if expr.op == "!":
                return ast.IntLiteral(0 if value else 1)
        return ast.UnaryOp(expr.op, operand)
    if isinstance(expr, ast.BinaryOp):
        left = optimize_expr(expr.left)
        right = optimize_expr(expr.right)
        if expr.op == "&&":
            # Short-circuit simplifications
            if is_const_int(left):
                if const_value(left) == 0:
                    return ast.IntLiteral(0)  # 0 && x -> 0
                # left is non-zero true: a && b -> b != 0 (simplify to b)
                return optimize_expr(ast.UnaryOp("!", ast.UnaryOp("!", right)))
        if expr.op == "||":
            if is_const_int(left):
                if const_value(left) != 0:
                    return ast.IntLiteral(1)  # 1 || x -> 1
                # left is 0: 0 || b -> b != 0 (simplify to b)
                return optimize_expr(ast.UnaryOp("!", ast.UnaryOp("!", right)))
        if is_const_int(left) and is_const_int(right):
            lval = const_value(left)
            rval = const_value(right)
            if expr.op == "+":
                return ast.IntLiteral(lval + rval)
            if expr.op == "-":
                return ast.IntLiteral(lval - rval)
            if expr.op == "*":
                return ast.IntLiteral(lval * rval)
            if expr.op == "/":
                if rval == 0:
                    return ast.IntLiteral(0)
                return ast.IntLiteral(int(lval / rval))  # truncate toward zero (C semantics)
            if expr.op == "%":
                if rval == 0:
                    return ast.IntLiteral(0)
                return ast.IntLiteral(lval - (int(lval / rval) * rval))  # C semantics: (a/b)*b + a%b == a
            if expr.op in COMPARE_OPS:
                return ast.IntLiteral(1 if eval_compare(expr.op, lval, rval) else 0)
            if expr.op == "&&":
                return ast.IntLiteral(1 if (lval and rval) else 0)
            if expr.op == "||":
                return ast.IntLiteral(1 if (lval or rval) else 0)
        return ast.BinaryOp(expr.op, left, right)
    if isinstance(expr, ast.Call):
        return ast.Call(expr.name, [optimize_expr(arg) for arg in expr.args])
    if isinstance(expr, ast.ArrayAccess):
        return ast.ArrayAccess(optimize_expr(expr.array), optimize_expr(expr.index))
    if isinstance(expr, ast.ArrayAssign):
        return ast.ArrayAssign(expr.name, optimize_expr(expr.index), optimize_expr(expr.value))
    if isinstance(expr, ast.Deref):
        operand = optimize_expr(expr.operand)
        # *&x -> x
        if isinstance(operand, ast.AddrOf):
            return operand.operand
        return ast.Deref(operand)
    if isinstance(expr, ast.AddrOf):
        operand = optimize_expr(expr.operand)
        # &*p -> p
        if isinstance(operand, ast.Deref):
            return operand.operand
        return ast.AddrOf(operand)
    if isinstance(expr, ast.DerefAssign):
        return ast.DerefAssign(optimize_expr(expr.ptr), optimize_expr(expr.value))
    return expr


def is_const_int(expr: ast.Expr | None) -> bool:
    return isinstance(expr, ast.IntLiteral)


def const_value(expr: ast.Expr) -> int:
    assert isinstance(expr, ast.IntLiteral)
    return expr.value


def eval_compare(op: str, left: int, right: int) -> bool:
    if op == "<":
        return left < right
    if op == "<=":
        return left <= right
    if op == ">":
        return left > right
    if op == ">=":
        return left >= right
    if op == "==":
        return left == right
    if op == "!=":
        return left != right
    raise ValueError(f"unsupported compare op: {op}")
