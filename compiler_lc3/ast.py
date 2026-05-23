from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Union


@dataclass
class Program:
    globals: List["GlobalDecl"]
    functions: List["FunctionDef"]


@dataclass
class GlobalDecl:
    name: str
    init: Optional[int]


@dataclass
class FunctionDef:
    name: str
    params: List[str]
    body: "Block"


@dataclass
class Block:
    items: List["BlockItem"] = field(default_factory=list)


BlockItem = Union["VarDecl", "Statement"]


@dataclass
class VarDecl:
    name: str
    init: Optional["Expr"]


class Statement:
    pass


@dataclass
class ExprStmt(Statement):
    expr: "Expr"


@dataclass
class IfStmt(Statement):
    condition: "Expr"
    then_branch: Statement
    else_branch: Optional[Statement]


@dataclass
class WhileStmt(Statement):
    condition: "Expr"
    body: Statement


@dataclass
class ForStmt(Statement):
    init: Optional["Expr"]
    condition: Optional["Expr"]
    step: Optional["Expr"]
    body: Statement


@dataclass
class BreakStmt(Statement):
    pass


@dataclass
class ContinueStmt(Statement):
    pass


@dataclass
class ReturnStmt(Statement):
    expr: Optional["Expr"]


@dataclass
class BlockStmt(Statement):
    block: Block


class Expr:
    pass


@dataclass
class IntLiteral(Expr):
    value: int


@dataclass
class StringLiteral(Expr):
    value: str


@dataclass
class Variable(Expr):
    name: str


@dataclass
class Assign(Expr):
    name: str
    value: Expr


@dataclass
class UnaryOp(Expr):
    op: str
    operand: Expr


@dataclass
class IncDecOp(Expr):
    name: str
    delta: int
    is_postfix: bool


@dataclass
class BinaryOp(Expr):
    op: str
    left: Expr
    right: Expr


@dataclass
class Call(Expr):
    name: str
    args: List[Expr]
