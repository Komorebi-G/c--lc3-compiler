from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Union


@dataclass(frozen=True)
class Type:
    base: str          # "int", "char", "bool"
    ptr_depth: int = 0  # 0=scalar, 1=*, 2=**...

    def __str__(self) -> str:
        return self.base + "*" * self.ptr_depth

    @property
    def is_ptr(self) -> bool:
        return self.ptr_depth > 0

    def pointee(self) -> "Type":
        assert self.ptr_depth > 0
        return Type(self.base, self.ptr_depth - 1)


TYPE_INT = Type("int", 0)
TYPE_CHAR = Type("char", 0)
TYPE_BOOL = Type("bool", 0)


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


BlockItem = Union["VarDecl", "ArrayDecl", "Statement"]


@dataclass
class VarDecl:
    name: str
    init: Optional["Expr"]
    var_type: Type = field(default=TYPE_INT)


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


@dataclass
class ArrayAccess(Expr):
    """Array indexing: arr[index]"""
    array: Expr
    index: Expr


@dataclass
class ArrayDecl:
    """Array declaration: int arr[10]; or int arr[10] = {1, 2};"""
    name: str
    size: int
    init_list: Optional[List[Expr]] = None


@dataclass
class ArrayAssign(Expr):
    """Assignment to array element: arr[index] = value"""
    name: str
    index: Expr
    value: Expr


@dataclass
class Deref(Expr):
    """Pointer dereference: *ptr"""
    operand: Expr


@dataclass
class AddrOf(Expr):
    """Address-of: &var"""
    operand: Expr


@dataclass
class DerefAssign(Expr):
    """Assignment through pointer: *ptr = value"""
    ptr: Expr
    value: Expr
