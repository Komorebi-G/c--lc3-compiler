from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from . import ast


class CodegenError(ValueError):
    pass


BUILTINS = {"getchar", "putchar", "puts"}
COMPARE_OPS = {"<", "<=", ">", ">=", "==", "!="}
BARE_INSTRUCTIONS = {"RET", "GETC", "OUT", "PUTS", "HALT"}


@dataclass
class LoopLabels:
    break_label: str
    continue_label: str


class FunctionContext:
    def __init__(self, generator: "CodeGenerator", func: ast.FunctionDef) -> None:
        self.generator = generator
        self.func = func
        self.lines: List[str] = []
        self.var_offsets: Dict[str, int] = {}
        self.param_names = list(func.params)
        self.local_names: List[str] = []
        self.local_count = 0
        self.loop_stack: List[LoopLabels] = []
        self.end_label = self.generator.new_label(f"{func.name}_end")
        self.use_frame_pointer = True
        self.save_r7 = True
        self.saved_regs: List[str] = []
        self.param_base_reg = "R5"
        self.param_offset_base = 2
        self.direct_return_stmt_id: Optional[int] = None
        self.zero_init_locals: Set[str] = set()

    def emit(self, line: str) -> None:
        self.lines.append(line)

    def emit_label(self, label: str) -> None:
        self.lines.append(f"{label}")

    def emit_comment(self, text: str) -> None:
        self.generator._emit_comment(self.lines, text)

    def alloc_local(self, name: str) -> int:
        if name in self.local_names or name in self.param_names:
            raise CodegenError(f"duplicate local or parameter name: {name}")
        self.local_count += 1
        self.local_names.append(name)
        return -self.local_count

    def lookup(self, name: str) -> Optional[int]:
        return self.var_offsets.get(name)

    def configure_frame(self, *, use_frame_pointer: bool, save_r7: bool, saved_regs: List[str]) -> None:
        self.use_frame_pointer = use_frame_pointer
        self.save_r7 = save_r7
        self.saved_regs = list(saved_regs)
        self.var_offsets = {}
        self.param_base_reg = "R5" if use_frame_pointer else "R6"
        if use_frame_pointer:
            self.param_offset_base = 2 if save_r7 else 1
        else:
            self.param_offset_base = len(self.saved_regs) + (1 if save_r7 else 0)
        for index, param in enumerate(self.param_names):
            self.var_offsets[param] = self.param_offset_base + index
        local_base = len(self.saved_regs) if use_frame_pointer else 0
        for index, name in enumerate(self.local_names, start=1):
            self.var_offsets[name] = -(local_base + index)


class CodeGenerator:
    def __init__(self, *, debug_comments: bool = False, beginner_style: bool = False) -> None:
        self.debug_comments = debug_comments
        self.beginner_style = beginner_style
        self.label_counter = 0
        self.literal_counter = 0
        self.string_counter = 0
        self.literal_labels: Dict[int, str] = {}
        self.string_labels: Dict[str, str] = {}
        self.globals: Dict[str, str] = {}
        self.global_inits: Dict[str, int] = {}
        self.functions: Dict[str, ast.FunctionDef] = {}
        self.function_labels: Dict[str, str] = {}
        self.expr_registers = ["R0", "R1", "R2", "R3", "R4"]
        self.beginner_program_uses_stack = False

    def generate(self, program: ast.Program) -> str:
        self._collect_globals(program)
        self._collect_functions(program)
        if "main" not in self.functions:
            raise CodegenError("program must define int main()")
        if self.beginner_style:
            self.beginner_program_uses_stack = self._program_uses_stack_in_beginner_style(program)

        lines: List[str] = []
        lines.append(".ORIG x3000")
        if not self.beginner_style:
            lines.extend(self._emit_startup())
        ordered_functions = [self.functions["main"]] + [func for func in program.functions if func.name != "main"]
        for func in ordered_functions:
            lines.extend(self._emit_function(func))
        lines.extend(self._emit_global_data())
        lines.extend(self._emit_literals())
        lines = self._optimize_assembly_lines(lines)
        lines.append(".END")
        return "\n".join(lines) + "\n"

    def _emit_startup(self) -> List[str]:
        lines: List[str] = []
        self._emit_comment(lines, "程序入口")
        self._append_instruction(lines, "    LD R6, STACK_TOP", "初始化运行时栈指针")
        self._append_instruction(lines, "    AND R5, R5, #0", "进入 main 前先清空帧指针")
        self._append_instruction(lines, f"    JSR {self.function_labels['main']}", "调用 C 语言入口函数 main")
        self._append_instruction(lines, "    HALT", "main 返回后停止机器")
        return lines

    def new_label(self, prefix: str) -> str:
        label = f"{prefix}_{self.label_counter}"
        self.label_counter += 1
        return label

    def _emit_comment(self, lines: List[str], text: str) -> None:
        if not self.debug_comments:
            return
        for part in text.splitlines():
            if part:
                lines.append(f"; {part}")
            else:
                lines.append(";")

    def _append_instruction(self, lines: List[str], instruction: str, comment: Optional[str] = None) -> None:
        if self.debug_comments and comment:
            lines.append(f"{instruction:<24} ; {comment}")
        else:
            lines.append(instruction)

    def _optimize_assembly_lines(self, lines: List[str]) -> List[str]:
        lines = self._remove_unused_labels(lines)
        optimized: List[str] = []
        total = len(lines)
        for index, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("BRnzp "):
                target = stripped.split(None, 1)[1].split(";", 1)[0].strip()
                next_index = index + 1
                while next_index < total and (
                    not lines[next_index].strip() or lines[next_index].lstrip().startswith(";")
                ):
                    next_index += 1
                if next_index < total and lines[next_index].strip() == target:
                    continue
            optimized.append(line)
        return optimized

    def _remove_unused_labels(self, lines: List[str]) -> List[str]:
        referenced: set[str] = set()
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith(";"):
                continue
            if stripped.endswith(".FILL xF000"):
                continue
            if stripped.startswith("."):
                continue
            if " " in stripped:
                parts = stripped.split()
                op = parts[0]
                if op.startswith("BR") or op in {"JSR", "LD", "LEA"}:
                    target = parts[1].split(";", 1)[0].strip()
                    if target and not target.startswith("#") and not target.startswith("R") and target != "STACK_TOP":
                        referenced.add(target)

        kept: List[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped and " " not in stripped and not stripped.startswith(";") and not stripped.startswith("."):
                if (
                    stripped in referenced
                    or stripped in BARE_INSTRUCTIONS
                    or stripped.startswith("LC3_BUILTIN_")
                    or stripped in self.function_labels.values()
                ):
                    kept.append(line)
                continue
            kept.append(line)
        return kept

    def _expr_to_text(self, expr: ast.Expr) -> str:
        if isinstance(expr, ast.IntLiteral):
            return str(expr.value)
        if isinstance(expr, ast.StringLiteral):
            return '"' + expr.value.replace("\n", "\\n").replace("\t", "\\t") + '"'
        if isinstance(expr, ast.Variable):
            return expr.name
        if isinstance(expr, ast.Assign):
            return f"{expr.name} = {self._expr_to_text(expr.value)}"
        if isinstance(expr, ast.UnaryOp):
            return f"{expr.op}{self._expr_to_text(expr.operand)}"
        if isinstance(expr, ast.IncDecOp):
            op = "++" if expr.delta > 0 else "--"
            return f"{expr.name}{op}" if expr.is_postfix else f"{op}{expr.name}"
        if isinstance(expr, ast.BinaryOp):
            return f"{self._expr_to_text(expr.left)} {expr.op} {self._expr_to_text(expr.right)}"
        if isinstance(expr, ast.Call):
            return f"{expr.name}(" + ", ".join(self._expr_to_text(arg) for arg in expr.args) + ")"
        return "<expr>"

    def _stmt_to_text(self, stmt: ast.Statement) -> str:
        if isinstance(stmt, ast.ExprStmt):
            return self._expr_to_text(stmt.expr) + ";"
        if isinstance(stmt, ast.BreakStmt):
            return "break;"
        if isinstance(stmt, ast.ContinueStmt):
            return "continue;"
        if isinstance(stmt, ast.ReturnStmt):
            if stmt.expr is None:
                return "return;"
            return f"return {self._expr_to_text(stmt.expr)};"
        if isinstance(stmt, ast.IfStmt):
            return f"if ({self._expr_to_text(stmt.condition)}) ..."
        if isinstance(stmt, ast.WhileStmt):
            return f"while ({self._expr_to_text(stmt.condition)}) ..."
        if isinstance(stmt, ast.ForStmt):
            init = self._expr_to_text(stmt.init) if stmt.init is not None else ""
            cond = self._expr_to_text(stmt.condition) if stmt.condition is not None else ""
            step = self._expr_to_text(stmt.step) if stmt.step is not None else ""
            return f"for ({init}; {cond}; {step}) ..."
        if isinstance(stmt, ast.BlockStmt):
            return "{ ... }"
        return "<stmt>"

    def _format_var_location(self, offset: int) -> str:
        if offset >= 0:
            return f"[R5 + {offset}]"
        return f"[R5 - {-offset}]"

    def literal_label(self, value: int) -> str:
        if value not in self.literal_labels:
            self.literal_labels[value] = f"LC_INT_{self.literal_counter}"
            self.literal_counter += 1
        return self.literal_labels[value]

    def string_label(self, value: str) -> str:
        if value not in self.string_labels:
            self.string_labels[value] = f"LC_STR_{self.string_counter}"
            self.string_counter += 1
        return self.string_labels[value]

    def _collect_globals(self, program: ast.Program) -> None:
        for decl in program.globals:
            if decl.name in self.globals:
                raise CodegenError(f"duplicate global: {decl.name}")
            if decl.name in BUILTINS:
                raise CodegenError(f"global name conflicts with builtin: {decl.name}")
            self.globals[decl.name] = f"G_{decl.name}"
            self.global_inits[decl.name] = decl.init if decl.init is not None else 0

    def _collect_functions(self, program: ast.Program) -> None:
        for func in program.functions:
            if func.name in BUILTINS:
                raise CodegenError(f"function name conflicts with builtin: {func.name}")
            if func.name in self.functions:
                raise CodegenError(f"duplicate function: {func.name}")
            self.functions[func.name] = func
            self.function_labels[func.name] = "main" if func.name == "main" else f"FN_{func.name}"

    def _emit_function(self, func: ast.FunctionDef) -> List[str]:
        has_calls = self._block_has_calls(func.body)
        is_main = func.name == "main"
        last_stmt = self._last_executable_stmt(func.body)
        direct_return_stmt_id = id(last_stmt) if isinstance(last_stmt, ast.ReturnStmt) and self._count_returns_in_block(func.body) == 1 else None

        preview_ctx = FunctionContext(self, func)
        self._collect_locals(preview_ctx, func.body)
        preview_ctx.configure_frame(use_frame_pointer=True, save_r7=(has_calls and not self._main_is_program_entry(is_main)), saved_regs=[])
        preview_ctx.direct_return_stmt_id = direct_return_stmt_id
        self._emit_block(preview_ctx, func.body)

        saved_regs = self._collect_modified_callee_regs(preview_ctx.lines)
        if self._main_is_program_entry(is_main):
            saved_regs = []
        ctx = FunctionContext(self, func)
        self._collect_locals(ctx, func.body)
        save_r7 = has_calls and not self._main_is_program_entry(is_main)
        use_frame_pointer = ctx.local_count > 0 or bool(saved_regs) or save_r7
        ctx.configure_frame(use_frame_pointer=use_frame_pointer, save_r7=save_r7, saved_regs=saved_regs)
        ctx.direct_return_stmt_id = direct_return_stmt_id

        lines: List[str] = [self.function_labels[func.name]]
        self._emit_comment(lines, f"函数 {func.name}(" + ", ".join(f"int {param}" for param in func.params) + ")")
        if self._main_is_program_entry(is_main) and self.beginner_program_uses_stack:
            self._append_instruction(lines, "    LD R6, STACK_TOP", "初学者模式下仅在确实需要时初始化栈指针")
            self._append_instruction(lines, "    AND R5, R5, #0", "初学者模式下仅在确实需要时清空帧指针")
        if ctx.save_r7:
            lines.extend(
                [
                    "    ADD R6, R6, #-1",
                    "    STR R7, R6, #0",
                ]
            )
        if ctx.use_frame_pointer:
            lines.extend(
                [
                    "    ADD R6, R6, #-1",
                    "    STR R5, R6, #0",
                    "    ADD R5, R6, #0",
                ]
            )
        for reg in ctx.saved_regs:
            self._append_instruction(lines, "    ADD R6, R6, #-1", f"为保存寄存器 {reg} 预留栈槽")
            self._append_instruction(lines, f"    STR {reg}, R6, #0", f"保存被调用者负责恢复的寄存器 {reg}")
        if self.debug_comments:
            self._emit_function_layout(lines, ctx)
        if ctx.use_frame_pointer:
            for _ in range(ctx.local_count):
                self._append_instruction(lines, "    ADD R6, R6, #-1", "为一个局部变量分配栈槽")
            self._init_locals_zero(ctx)
        self._emit_block(ctx, func.body)
        lines.extend(ctx.lines)
        lines.append(f"{ctx.end_label}")
        if ctx.use_frame_pointer:
            for index, reg in enumerate(ctx.saved_regs, start=1):
                self._append_instruction(lines, f"    LDR {reg}, R5, #-{index}", f"恢复被调用者保存的寄存器 {reg}")
            lines.extend(
                [
                    "    ADD R6, R5, #0",
                    "    LDR R5, R6, #0",
                    "    ADD R6, R6, #1",
                ]
            )
        if ctx.save_r7:
            lines.extend(
                [
                    "    LDR R7, R6, #0",
                    "    ADD R6, R6, #1",
                ]
            )
        lines.append("    HALT" if self._main_is_program_entry(is_main) else "    RET")
        return lines

    def _main_is_program_entry(self, is_main: bool) -> bool:
        return self.beginner_style and is_main

    def _program_uses_stack_in_beginner_style(self, program: ast.Program) -> bool:
        ordered_functions = [self.functions["main"]] + [func for func in program.functions if func.name != "main"]
        for func in ordered_functions:
            if self._function_needs_stack(func):
                return True
        return False

    def _function_needs_stack(self, func: ast.FunctionDef) -> bool:
        has_calls = self._block_has_calls(func.body)
        is_entry_main = self.beginner_style and func.name == "main"
        preview_ctx = FunctionContext(self, func)
        self._collect_locals(preview_ctx, func.body)
        preview_ctx.configure_frame(
            use_frame_pointer=True,
            save_r7=(has_calls and not is_entry_main),
            saved_regs=[],
        )
        last_stmt = self._last_executable_stmt(func.body)
        if isinstance(last_stmt, ast.ReturnStmt) and self._count_returns_in_block(func.body) == 1:
            preview_ctx.direct_return_stmt_id = id(last_stmt)
        self._emit_block(preview_ctx, func.body)
        saved_regs = self._collect_modified_callee_regs(preview_ctx.lines)
        if self._main_is_program_entry(func.name == "main"):
            saved_regs = []
        if preview_ctx.local_count > 0:
            return True
        if saved_regs:
            return True
        if has_calls and not is_entry_main:
            return True
        return self._lines_use_stack(preview_ctx.lines)

    def _lines_use_stack(self, lines: List[str]) -> bool:
        for line in lines:
            stripped = line.split(";", 1)[0].strip()
            if not stripped:
                continue
            if "R6" in stripped:
                return True
        return False

    def _emit_function_layout(self, lines: List[str], ctx: FunctionContext) -> None:
        self._emit_comment(lines, "栈帧布局")
        if ctx.use_frame_pointer:
            self._emit_comment(lines, "  [R5 + 0] 调用者保存的旧帧指针")
            if ctx.save_r7:
                self._emit_comment(lines, "  [R5 + 1] 保存的返回地址")
            for index, reg in enumerate(ctx.saved_regs, start=1):
                self._emit_comment(lines, f"  [R5 - {index}] 保存的寄存器 {reg}")
        elif ctx.save_r7:
            self._emit_comment(lines, "  [R6 + 0] 保存的返回地址")
        else:
            self._emit_comment(lines, "  本函数是叶子函数，不建立栈帧")
        for name in ctx.param_names:
            offset = ctx.var_offsets[name]
            self._emit_comment(lines, f"  {self._format_named_location(ctx, offset)} {name}")
        for name, offset in ctx.var_offsets.items():
            if name in ctx.param_names:
                continue
            self._emit_comment(lines, f"  {self._format_named_location(ctx, offset)} {name}")

    def _format_named_location(self, ctx: FunctionContext, offset: int) -> str:
        if ctx.use_frame_pointer:
            return self._format_var_location(offset)
        return f"[R6 + {offset}]"

    def _collect_locals(self, ctx: FunctionContext, block: ast.Block) -> None:
        for item in block.items:
            if isinstance(item, ast.VarDecl):
                ctx.alloc_local(item.name)
                if isinstance(item.init, ast.IntLiteral) and item.init.value == 0:
                    ctx.zero_init_locals.add(item.name)
            elif isinstance(item, ast.BlockStmt):
                self._collect_locals(ctx, item.block)
            elif isinstance(item, ast.IfStmt):
                self._collect_stmt_locals(ctx, item.then_branch)
                if item.else_branch is not None:
                    self._collect_stmt_locals(ctx, item.else_branch)
            elif isinstance(item, ast.WhileStmt):
                self._collect_stmt_locals(ctx, item.body)
            elif isinstance(item, ast.ForStmt):
                self._collect_stmt_locals(ctx, item.body)

    def _collect_stmt_locals(self, ctx: FunctionContext, stmt: ast.Statement) -> None:
        if isinstance(stmt, ast.BlockStmt):
            self._collect_locals(ctx, stmt.block)
        elif isinstance(stmt, ast.IfStmt):
            self._collect_stmt_locals(ctx, stmt.then_branch)
            if stmt.else_branch is not None:
                self._collect_stmt_locals(ctx, stmt.else_branch)
        elif isinstance(stmt, ast.WhileStmt):
            self._collect_stmt_locals(ctx, stmt.body)
        elif isinstance(stmt, ast.ForStmt):
            self._collect_stmt_locals(ctx, stmt.body)

    def _block_has_calls(self, block: ast.Block) -> bool:
        for item in block.items:
            if isinstance(item, ast.VarDecl):
                if item.init is not None and self._expr_has_calls(item.init):
                    return True
            elif isinstance(item, ast.Statement) and self._stmt_has_calls(item):
                return True
        return False

    def _stmt_has_calls(self, stmt: ast.Statement) -> bool:
        if isinstance(stmt, ast.ExprStmt):
            return self._expr_has_calls(stmt.expr)
        if isinstance(stmt, ast.BlockStmt):
            return self._block_has_calls(stmt.block)
        if isinstance(stmt, ast.IfStmt):
            return (
                self._expr_has_calls(stmt.condition)
                or self._stmt_has_calls(stmt.then_branch)
                or (stmt.else_branch is not None and self._stmt_has_calls(stmt.else_branch))
            )
        if isinstance(stmt, ast.WhileStmt):
            return self._expr_has_calls(stmt.condition) or self._stmt_has_calls(stmt.body)
        if isinstance(stmt, ast.ForStmt):
            return (
                (stmt.init is not None and self._expr_has_calls(stmt.init))
                or (stmt.condition is not None and self._expr_has_calls(stmt.condition))
                or (stmt.step is not None and self._expr_has_calls(stmt.step))
                or self._stmt_has_calls(stmt.body)
            )
        if isinstance(stmt, ast.ReturnStmt):
            return stmt.expr is not None and self._expr_has_calls(stmt.expr)
        return False

    def _count_returns_in_block(self, block: ast.Block) -> int:
        total = 0
        for item in block.items:
            if isinstance(item, ast.Statement):
                total += self._count_returns_in_stmt(item)
        return total

    def _count_returns_in_stmt(self, stmt: ast.Statement) -> int:
        if isinstance(stmt, ast.ReturnStmt):
            return 1
        if isinstance(stmt, ast.BlockStmt):
            return self._count_returns_in_block(stmt.block)
        if isinstance(stmt, ast.IfStmt):
            total = self._count_returns_in_stmt(stmt.then_branch)
            if stmt.else_branch is not None:
                total += self._count_returns_in_stmt(stmt.else_branch)
            return total
        if isinstance(stmt, ast.WhileStmt):
            return self._count_returns_in_stmt(stmt.body)
        if isinstance(stmt, ast.ForStmt):
            return self._count_returns_in_stmt(stmt.body)
        return 0

    def _last_executable_stmt(self, block: ast.Block) -> Optional[ast.Statement]:
        for item in reversed(block.items):
            if isinstance(item, ast.Statement):
                return item
        return None

    def _collect_modified_callee_regs(self, lines: List[str]) -> List[str]:
        modified: List[str] = []
        seen: set[str] = set()
        for line in lines:
            reg = self._written_register(line)
            if reg in {"R1", "R2", "R3", "R4"} and reg not in seen:
                modified.append(reg)
                seen.add(reg)
        return modified

    def _written_register(self, line: str) -> Optional[str]:
        stripped = line.split(";", 1)[0].strip()
        if not stripped or stripped.startswith(".") or " " not in stripped:
            return None
        parts = stripped.replace(",", " ").split()
        if len(parts) < 2:
            return None
        opcode = parts[0]
        if opcode in {"ADD", "AND", "NOT", "LD", "LDR", "LEA"}:
            dest = parts[1]
            if dest.startswith("R"):
                return dest
        if opcode == "GETC":
            return "R0"
        return None

    def _expr_has_calls(self, expr: ast.Expr) -> bool:
        if isinstance(expr, ast.Call):
            return True
        if isinstance(expr, ast.Assign):
            return self._expr_has_calls(expr.value)
        if isinstance(expr, ast.UnaryOp):
            return self._expr_has_calls(expr.operand)
        if isinstance(expr, ast.BinaryOp):
            return self._expr_has_calls(expr.left) or self._expr_has_calls(expr.right)
        return False

    def _init_locals_zero(self, ctx: FunctionContext) -> None:
        for name in sorted(ctx.zero_init_locals, key=lambda local_name: ctx.var_offsets[local_name], reverse=True):
            offset = ctx.var_offsets[name]
            self._append_instruction(ctx.lines, "    AND R0, R0, #0", "准备 0，用于初始化局部变量")
            self._append_instruction(
                ctx.lines,
                f"    STR R0, R5, #{offset}",
                f"把变量 {name}（{self._format_var_location(offset)}）初始化为 0",
            )

    def _emit_store_init(self, ctx: FunctionContext, name: str, expr: ast.Expr) -> None:
        self._emit_expr(ctx, expr)
        self._emit_store_var(ctx, name, "R0")

    def _emit_block(self, ctx: FunctionContext, block: ast.Block) -> None:
        for item in block.items:
            if isinstance(item, ast.VarDecl):
                if item.init is not None:
                    if isinstance(item.init, ast.IntLiteral) and item.init.value == 0:
                        ctx.emit_comment(f"变量定义：int {item.name} = 0;")
                        ctx.emit_comment("这个变量已经在函数入口统一清零，这里不再重复生成赋值")
                    else:
                        ctx.emit_comment(f"变量定义：int {item.name} = {self._expr_to_text(item.init)};")
                        self._emit_store_init(ctx, item.name, item.init)
                continue
            self._emit_stmt(ctx, item)

    def _emit_stmt(self, ctx: FunctionContext, stmt: ast.Statement) -> None:
        if isinstance(stmt, ast.ExprStmt):
            ctx.emit_comment(self._stmt_to_text(stmt))
            self._emit_expr(ctx, stmt.expr)
            return
        if isinstance(stmt, ast.BlockStmt):
            ctx.emit_comment("进入代码块")
            self._emit_block(ctx, stmt.block)
            ctx.emit_comment("离开代码块")
            return
        if isinstance(stmt, ast.IfStmt):
            ctx.emit_comment(f"if ({self._expr_to_text(stmt.condition)})")
            if stmt.else_branch is None:
                end_label = self.new_label("ifend")
                self._emit_branch_if_false(ctx, stmt.condition, end_label)
                self._emit_stmt(ctx, stmt.then_branch)
                ctx.emit_label(end_label)
                ctx.emit_comment("if 结束")
                return

            else_label = self.new_label("else")
            end_label = self.new_label("ifend")
            self._emit_branch_if_false(ctx, stmt.condition, else_label)
            self._emit_stmt(ctx, stmt.then_branch)
            if not self._stmt_always_transfers(stmt.then_branch):
                self._append_instruction(ctx.lines, f"    BRnzp {end_label}", "then 分支结束后跳过 else 分支")
            ctx.emit_label(else_label)
            ctx.emit_comment("否则执行这里")
            self._emit_stmt(ctx, stmt.else_branch)
            ctx.emit_comment("if 结束")
            ctx.emit_label(end_label)
            return
        if isinstance(stmt, ast.WhileStmt):
            test_label = self.new_label("while_test")
            end_label = self.new_label("while_end")
            ctx.loop_stack.append(LoopLabels(end_label, test_label))
            ctx.emit_comment(f"while ({self._expr_to_text(stmt.condition)})")
            ctx.emit_label(test_label)
            self._emit_branch_if_false(ctx, stmt.condition, end_label)
            ctx.emit_comment("while 循环体")
            self._emit_stmt(ctx, stmt.body)
            self._append_instruction(ctx.lines, f"    BRnzp {test_label}", "跳回 while 条件重新判断")
            ctx.emit_label(end_label)
            ctx.emit_comment("while 结束")
            ctx.loop_stack.pop()
            return
        if isinstance(stmt, ast.ForStmt):
            test_label = self.new_label("for_test")
            step_label = self.new_label("for_step")
            end_label = self.new_label("for_end")
            init_text = self._expr_to_text(stmt.init) if stmt.init is not None else ""
            cond_text = self._expr_to_text(stmt.condition) if stmt.condition is not None else ""
            step_text = self._expr_to_text(stmt.step) if stmt.step is not None else ""
            ctx.emit_comment(f"for ({init_text}; {cond_text}; {step_text})")
            if stmt.init is not None:
                ctx.emit_comment("for 初始化部分")
                self._emit_expr(ctx, stmt.init)
            ctx.loop_stack.append(LoopLabels(end_label, step_label))
            ctx.emit_label(test_label)
            if stmt.condition is not None:
                ctx.emit_comment("for 条件判断")
                self._emit_branch_if_false(ctx, stmt.condition, end_label)
            ctx.emit_comment("for 循环体")
            self._emit_stmt(ctx, stmt.body)
            ctx.emit_label(step_label)
            if stmt.step is not None:
                ctx.emit_comment("for 步进部分")
                self._emit_expr(ctx, stmt.step)
            self._append_instruction(ctx.lines, f"    BRnzp {test_label}", "跳回 for 条件重新判断")
            ctx.emit_label(end_label)
            ctx.emit_comment("for 结束")
            ctx.loop_stack.pop()
            return
        if isinstance(stmt, ast.BreakStmt):
            if not ctx.loop_stack:
                raise CodegenError("break used outside loop")
            ctx.emit_comment("break;")
            self._append_instruction(ctx.lines, f"    BRnzp {ctx.loop_stack[-1].break_label}", "跳到当前循环的结束位置")
            return
        if isinstance(stmt, ast.ContinueStmt):
            if not ctx.loop_stack:
                raise CodegenError("continue used outside loop")
            ctx.emit_comment("continue;")
            self._append_instruction(
                ctx.lines,
                f"    BRnzp {ctx.loop_stack[-1].continue_label}",
                "直接进入当前循环的下一次迭代",
            )
            return
        if isinstance(stmt, ast.ReturnStmt):
            ctx.emit_comment(self._stmt_to_text(stmt))
            if stmt.expr is None:
                self._append_instruction(ctx.lines, "    AND R0, R0, #0", "返回 0")
            else:
                self._emit_expr(ctx, stmt.expr)
            if ctx.direct_return_stmt_id == id(stmt):
                ctx.emit_comment("这是函数末尾唯一的 return，直接落入函数收尾代码")
            else:
                self._append_instruction(ctx.lines, f"    BRnzp {ctx.end_label}", "跳到统一的函数收尾代码")
            return
        raise CodegenError(f"unsupported statement: {stmt}")

    def _stmt_always_transfers(self, stmt: ast.Statement) -> bool:
        if isinstance(stmt, (ast.ReturnStmt, ast.BreakStmt, ast.ContinueStmt)):
            return True
        if isinstance(stmt, ast.BlockStmt):
            for item in reversed(stmt.block.items):
                if isinstance(item, ast.VarDecl):
                    continue
                return self._stmt_always_transfers(item)
            return False
        if isinstance(stmt, ast.IfStmt) and stmt.else_branch is not None:
            return self._stmt_always_transfers(stmt.then_branch) and self._stmt_always_transfers(stmt.else_branch)
        return False

    def _emit_branch_if_false(self, ctx: FunctionContext, expr: ast.Expr, false_label: str) -> None:
        if isinstance(expr, ast.IntLiteral):
            if expr.value == 0:
                self._append_instruction(ctx.lines, f"    BRnzp {false_label}", "常量条件恒为假，直接跳转")
            return
        if isinstance(expr, ast.UnaryOp) and expr.op == "!":
            self._emit_branch_if_true(ctx, expr.operand, false_label)
            return
        if isinstance(expr, ast.BinaryOp) and expr.op in COMPARE_OPS:
            self._emit_compare_branch(ctx, expr, false_label, branch_on_false=True)
            return
        self._emit_expr(ctx, expr)
        self._append_instruction(ctx.lines, "    ADD R0, R0, #0", f"根据 {self._expr_to_text(expr)} 设置条件码")
        self._append_instruction(ctx.lines, f"    BRz {false_label}", "当 C 条件为假（0）时跳转")

    def _emit_branch_if_true(self, ctx: FunctionContext, expr: ast.Expr, true_label: str) -> None:
        if isinstance(expr, ast.IntLiteral):
            if expr.value != 0:
                self._append_instruction(ctx.lines, f"    BRnzp {true_label}", "常量条件恒为真，直接跳转")
            return
        if isinstance(expr, ast.UnaryOp) and expr.op == "!":
            self._emit_branch_if_false(ctx, expr.operand, true_label)
            return
        if isinstance(expr, ast.BinaryOp) and expr.op in COMPARE_OPS:
            self._emit_compare_branch(ctx, expr, true_label, branch_on_false=False)
            return
        self._emit_expr(ctx, expr)
        self._append_instruction(ctx.lines, "    ADD R0, R0, #0", f"根据 {self._expr_to_text(expr)} 设置条件码")
        self._append_instruction(ctx.lines, f"    BRnp {true_label}", "当 C 条件为真（非 0）时跳转")

    def _emit_compare_branch(self, ctx: FunctionContext, expr: ast.BinaryOp, label: str, *, branch_on_false: bool) -> None:
        self._emit_expr_into(ctx, expr.left, "R0", ["R1", "R2", "R3", "R4"])
        self._emit_expr_into(ctx, expr.right, "R1", ["R2", "R3", "R4"])
        self._append_instruction(ctx.lines, "    NOT R1, R1", "比较时先计算 左值 - 右值")
        self._append_instruction(ctx.lines, "    ADD R1, R1, #1", "R1 = -右值")
        self._append_instruction(
            ctx.lines,
            "    ADD R1, R0, R1",
            f"R1 = {self._expr_to_text(expr.left)} - {self._expr_to_text(expr.right)}",
        )
        branch = self._compare_branch_opcode(expr.op, branch_on_false=branch_on_false)
        desc = "假" if branch_on_false else "真"
        self._append_instruction(ctx.lines, f"    {branch} {label}", f"当 {self._expr_to_text(expr)} 为{desc}时跳转")

    def _compare_branch_opcode(self, op: str, *, branch_on_false: bool) -> str:
        true_map = {
            "<": "BRn",
            "<=": "BRnz",
            ">": "BRp",
            ">=": "BRzp",
            "==": "BRz",
            "!=": "BRnp",
        }
        false_map = {
            "<": "BRzp",
            "<=": "BRp",
            ">": "BRnz",
            ">=": "BRn",
            "==": "BRnp",
            "!=": "BRz",
        }
        return (false_map if branch_on_false else true_map)[op]

    def _emit_expr(self, ctx: FunctionContext, expr: ast.Expr) -> None:
        self._emit_expr_into(ctx, expr, "R0", ["R1", "R2", "R3", "R4"])

    def _emit_expr_into(self, ctx: FunctionContext, expr: ast.Expr, target: str, scratch: List[str]) -> None:
        if isinstance(expr, ast.IntLiteral):
            self._emit_load_constant(ctx, target, expr.value)
            return
        if isinstance(expr, ast.StringLiteral):
            label = self.string_label(expr.value)
            self._append_instruction(
                ctx.lines,
                f"    LEA {target}, {label}",
                f"{target} = 字符串字面量 {self._expr_to_text(expr)} 的地址",
            )
            return
        if isinstance(expr, ast.Variable):
            self._emit_load_var(ctx, expr.name, target)
            return
        if isinstance(expr, ast.Assign):
            if self._emit_simple_assignment(ctx, expr, target):
                return
            self._emit_expr_into(ctx, expr.value, target, scratch)
            self._emit_store_var(ctx, expr.name, target)
            return
        if isinstance(expr, ast.IncDecOp):
            self._emit_inc_dec(ctx, expr, target)
            return
        if isinstance(expr, ast.UnaryOp):
            self._emit_expr_into(ctx, expr.operand, target, scratch)
            if expr.op == "-":
                self._append_instruction(ctx.lines, f"    NOT {target}, {target}", "开始做补码取负")
                self._append_instruction(
                    ctx.lines,
                    f"    ADD {target}, {target}, #1",
                    f"{target} = -({self._expr_to_text(expr.operand)})",
                )
                return
            if expr.op == "!":
                true_label = self.new_label("not_true")
                end_label = self.new_label("not_end")
                self._append_instruction(
                    ctx.lines,
                    f"    ADD {target}, {target}, #0",
                    f"判断 {self._expr_to_text(expr.operand)} 是否为 0",
                )
                self._append_instruction(ctx.lines, f"    BRz {true_label}", "如果是 0，则逻辑非结果应为 1")
                self._append_instruction(ctx.lines, f"    AND {target}, {target}, #0", "非 0 的逻辑非结果为 0")
                self._append_instruction(ctx.lines, f"    BRnzp {end_label}", "跳过逻辑非为真的分支")
                ctx.emit_label(true_label)
                self._append_instruction(ctx.lines, f"    AND {target}, {target}, #0", f"先清空 {target}，再生成逻辑真")
                self._append_instruction(ctx.lines, f"    ADD {target}, {target}, #1", "逻辑非结果为 1")
                ctx.emit_label(end_label)
                return
            raise CodegenError(f"unsupported unary operator: {expr.op}")
        if isinstance(expr, ast.BinaryOp):
            self._emit_binary(ctx, expr, target, scratch)
            return
        if isinstance(expr, ast.Call):
            self._emit_call(ctx, expr)
            if target != "R0":
                self._append_instruction(ctx.lines, f"    ADD {target}, R0, #0", f"把返回值复制到 {target}")
            return
        raise CodegenError(f"unsupported expression: {expr}")

    def _emit_simple_assignment(self, ctx: FunctionContext, expr: ast.Assign, target: str) -> bool:
        value = expr.value
        if isinstance(value, ast.IntLiteral):
            self._emit_load_constant(ctx, target, value.value)
            self._emit_store_var(ctx, expr.name, target)
            return True

        if not isinstance(value, ast.BinaryOp) or value.op not in {"+", "-"}:
            return False

        base_var: Optional[str] = None
        delta: Optional[int] = None

        if isinstance(value.left, ast.Variable) and value.left.name == expr.name and isinstance(value.right, ast.IntLiteral):
            base_var = expr.name
            delta = value.right.value if value.op == "+" else -value.right.value
        elif value.op == "+" and isinstance(value.right, ast.Variable) and value.right.name == expr.name and isinstance(value.left, ast.IntLiteral):
            base_var = expr.name
            delta = value.left.value

        if base_var is None or delta is None:
            return False

        if delta < -16 or delta > 15:
            return False

        self._emit_load_var(ctx, base_var, target)
        if delta != 0:
            self._append_instruction(ctx.lines, f"    ADD {target}, {target}, #{delta}", f"{target} = {expr.name} {'+' if delta >= 0 else '-'} {abs(delta)}")
        self._emit_store_var(ctx, expr.name, target)
        return True

    def _emit_inc_dec(self, ctx: FunctionContext, expr: ast.IncDecOp, target: str) -> None:
        self._emit_load_var(ctx, expr.name, target)
        if expr.is_postfix:
            update_reg = "R1" if target != "R1" else "R2"
            self._append_instruction(ctx.lines, f"    ADD {update_reg}, {target}, #0", f"{update_reg} = {expr.name} 的旧值")
            self._append_instruction(
                ctx.lines,
                f"    ADD {update_reg}, {update_reg}, #{expr.delta}",
                f"{update_reg} = {self._expr_to_text(expr)} 更新后的值",
            )
            self._emit_store_var(ctx, expr.name, update_reg)
            return
        self._append_instruction(
            ctx.lines,
            f"    ADD {target}, {target}, #{expr.delta}",
            f"{target} = {self._expr_to_text(expr)}",
        )
        self._emit_store_var(ctx, expr.name, target)

    def _emit_binary(self, ctx: FunctionContext, expr: ast.BinaryOp, target: str, scratch: List[str]) -> None:
        ctx.emit_comment(f"计算 {self._expr_to_text(expr)}")
        if not scratch:
            self._emit_binary_with_stack_fallback(ctx, expr, target)
            return

        right_reg = scratch[0]
        next_scratch = [reg for reg in scratch[1:] if reg != target]
        self._emit_expr_into(ctx, expr.left, target, scratch)
        self._emit_expr_into(ctx, expr.right, right_reg, next_scratch)

        if expr.op == "+":
            self._append_instruction(ctx.lines, f"    ADD {target}, {target}, {right_reg}", f"{target} = {self._expr_to_text(expr)}")
            return
        if expr.op == "-":
            self._append_instruction(ctx.lines, f"    NOT {right_reg}, {right_reg}", "减法先把右操作数取补码相反数")
            self._append_instruction(ctx.lines, f"    ADD {right_reg}, {right_reg}, #1", "完成补码取负")
            self._append_instruction(ctx.lines, f"    ADD {target}, {target}, {right_reg}", f"{target} = {self._expr_to_text(expr)}")
            return

        self._append_instruction(ctx.lines, f"    NOT {right_reg}, {right_reg}", "比较时先计算 左值 - 右值")
        self._append_instruction(ctx.lines, f"    ADD {right_reg}, {right_reg}, #1", f"{right_reg} = -右值")
        self._append_instruction(
            ctx.lines,
            f"    ADD {right_reg}, {target}, {right_reg}",
            f"{right_reg} = {self._expr_to_text(expr.left)} - {self._expr_to_text(expr.right)}",
        )
        true_label = self.new_label("cmp_true")
        end_label = self.new_label("cmp_end")
        branch = {
            "<": "BRn",
            "<=": "BRnz",
            ">": "BRp",
            ">=": "BRzp",
            "==": "BRz",
            "!=": "BRnp",
        }.get(expr.op)
        if branch is None:
            raise CodegenError(f"unsupported binary operator: {expr.op}")
        self._append_instruction(ctx.lines, f"    {branch} {true_label}", f"当 {self._expr_to_text(expr)} 为真时跳转")
        self._append_instruction(ctx.lines, f"    AND {target}, {target}, #0", "比较结果为假，记作 0")
        self._append_instruction(ctx.lines, f"    BRnzp {end_label}", "跳过比较为真的分支")
        ctx.emit_label(true_label)
        self._append_instruction(ctx.lines, f"    AND {target}, {target}, #0", f"先清空 {target}，再写入真值")
        self._append_instruction(ctx.lines, f"    ADD {target}, {target}, #1", "比较结果为真，记作 1")
        ctx.emit_label(end_label)

    def _emit_binary_with_stack_fallback(self, ctx: FunctionContext, expr: ast.BinaryOp, target: str) -> None:
        ctx.emit_comment("寄存器不足，回退到临时压栈求值")
        self._emit_expr_into(ctx, expr.left, target, [])
        self._push_reg(ctx, target)
        self._emit_expr_into(ctx, expr.right, target, [])
        self._append_instruction(ctx.lines, "    ADD R6, R6, #-1", "把右操作数暂存在栈上")
        self._append_instruction(ctx.lines, f"    STR {target}, R6, #0", "压入右操作数")
        self._append_instruction(ctx.lines, f"    LDR R1, R6, #1", f"R1 = 左操作数（{self._expr_to_text(expr.left)}）")
        self._append_instruction(ctx.lines, f"    LDR {target}, R6, #0", f"{target} = 右操作数（{self._expr_to_text(expr.right)}）")
        self._append_instruction(ctx.lines, "    ADD R6, R6, #2", "弹出两个临时操作数")

        if expr.op == "+":
            self._append_instruction(ctx.lines, f"    ADD {target}, R1, {target}", f"{target} = {self._expr_to_text(expr)}")
            return
        if expr.op == "-":
            self._append_instruction(ctx.lines, f"    NOT {target}, {target}", "减法先把右操作数取补码相反数")
            self._append_instruction(ctx.lines, f"    ADD {target}, {target}, #1", "完成补码取负")
            self._append_instruction(ctx.lines, f"    ADD {target}, R1, {target}", f"{target} = {self._expr_to_text(expr)}")
            return

        self._append_instruction(ctx.lines, f"    NOT {target}, {target}", "比较时先计算 左值 - 右值")
        self._append_instruction(ctx.lines, f"    ADD {target}, {target}, #1", f"{target} = -右值")
        self._append_instruction(
            ctx.lines,
            f"    ADD {target}, R1, {target}",
            f"{target} = {self._expr_to_text(expr.left)} - {self._expr_to_text(expr.right)}",
        )
        true_label = self.new_label("cmp_true")
        end_label = self.new_label("cmp_end")
        branch = {
            "<": "BRn",
            "<=": "BRnz",
            ">": "BRp",
            ">=": "BRzp",
            "==": "BRz",
            "!=": "BRnp",
        }.get(expr.op)
        if branch is None:
            raise CodegenError(f"unsupported binary operator: {expr.op}")
        self._append_instruction(ctx.lines, f"    {branch} {true_label}", f"当 {self._expr_to_text(expr)} 为真时跳转")
        self._append_instruction(ctx.lines, f"    AND {target}, {target}, #0", "比较结果为假，记作 0")
        self._append_instruction(ctx.lines, f"    BRnzp {end_label}", "跳过比较为真的分支")
        ctx.emit_label(true_label)
        self._append_instruction(ctx.lines, f"    AND {target}, {target}, #0", f"先清空 {target}，再写入真值")
        self._append_instruction(ctx.lines, f"    ADD {target}, {target}, #1", "比较结果为真，记作 1")
        ctx.emit_label(end_label)

    def _emit_call(self, ctx: FunctionContext, call: ast.Call) -> None:
        ctx.emit_comment(f"调用 {self._expr_to_text(call)}")
        if call.name in BUILTINS:
            if call.name == "getchar":
                if call.args:
                    raise CodegenError("getchar takes no arguments")
                self._append_instruction(ctx.lines, "    GETC", "直接调用 LC-3 的 GETC 读入一个字符")
            elif call.name in {"putchar", "puts"}:
                if len(call.args) != 1:
                    raise CodegenError(f"{call.name} takes exactly one argument")
                self._emit_expr(ctx, call.args[0])
                if call.name == "putchar":
                    self._append_instruction(ctx.lines, "    OUT", "直接调用 LC-3 的 OUT 输出 R0 中的字符")
                else:
                    self._append_instruction(ctx.lines, "    PUTS", "直接调用 LC-3 的 PUTS 输出 R0 指向的字符串")
                self._append_instruction(ctx.lines, "    AND R0, R0, #0", f"{call.name} 的返回值固定记作 0")
            else:
                raise CodegenError(f"unsupported builtin: {call.name}")
            return
        for arg in reversed(call.args):
            self._emit_expr(ctx, arg)
            self._push_reg(ctx, "R0")
        if call.name not in self.functions:
            raise CodegenError(f"undefined function: {call.name}")
        target = self.function_labels[call.name]
        self._append_instruction(ctx.lines, f"    JSR {target}", f"调用 {call.name}")
        if call.args:
            self._emit_add_imm(ctx, "R6", len(call.args))

    def _push_reg(self, ctx: FunctionContext, reg: str) -> None:
        self._append_instruction(ctx.lines, "    ADD R6, R6, #-1", "在栈上为一个临时值腾出空间")
        self._append_instruction(ctx.lines, f"    STR {reg}, R6, #0", f"把 {reg} 压栈")

    def _pick_address_reg(self, *reserved: str) -> str:
        for reg in ("R4", "R3", "R2", "R1", "R0"):
            if reg not in reserved:
                return reg
        raise CodegenError("no register available for address calculation")

    def _emit_load_var(self, ctx: FunctionContext, name: str, target: str) -> None:
        offset = ctx.lookup(name)
        if offset is not None:
            base_reg = ctx.param_base_reg if name in ctx.param_names else "R5"
            self._append_instruction(
                ctx.lines,
                f"    LDR {target}, {base_reg}, #{offset}",
                f"{target} = 变量 {name}，来自 {self._format_named_location(ctx, offset) if name in ctx.param_names else self._format_var_location(offset)}",
            )
            return
        if name in self.globals:
            addr_reg = self._pick_address_reg(target)
            self._append_instruction(ctx.lines, f"    LEA {addr_reg}, {self.globals[name]}", f"{addr_reg} = 全局变量 {name} 的地址")
            self._append_instruction(ctx.lines, f"    LDR {target}, {addr_reg}, #0", f"{target} = 全局变量 {name}")
            return
        raise CodegenError(f"undefined variable: {name}")

    def _emit_store_var(self, ctx: FunctionContext, name: str, source: str) -> None:
        offset = ctx.lookup(name)
        if offset is not None:
            base_reg = ctx.param_base_reg if name in ctx.param_names else "R5"
            self._append_instruction(
                ctx.lines,
                f"    STR {source}, {base_reg}, #{offset}",
                f"把 {source} 存回变量 {name}，位置是 {self._format_named_location(ctx, offset) if name in ctx.param_names else self._format_var_location(offset)}",
            )
            return
        if name in self.globals:
            addr_reg = self._pick_address_reg(source)
            self._append_instruction(ctx.lines, f"    LEA {addr_reg}, {self.globals[name]}", f"{addr_reg} = 全局变量 {name} 的地址")
            self._append_instruction(ctx.lines, f"    STR {source}, {addr_reg}, #0", f"把 {source} 存回全局变量 {name}")
            return
        raise CodegenError(f"undefined variable: {name}")

    def _emit_load_constant(self, ctx: FunctionContext, reg: str, value: int) -> None:
        if -16 <= value <= 15:
            self._append_instruction(ctx.lines, f"    AND {reg}, {reg}, #0", f"先清空 {reg}，再加载常量 {value}")
            if value != 0:
                self._append_instruction(ctx.lines, f"    ADD {reg}, {reg}, #{value}", f"{reg} = {value}")
            return
        self._append_instruction(ctx.lines, f"    LD {reg}, {self.literal_label(value)}", f"{reg} = 常量 {value}")

    def _emit_add_imm(self, ctx: FunctionContext, reg: str, value: int) -> None:
        while value > 15:
            self._append_instruction(ctx.lines, f"    ADD {reg}, {reg}, #15", f"先把 {reg} 增加 15")
            value -= 15
        while value < -16:
            self._append_instruction(ctx.lines, f"    ADD {reg}, {reg}, #-16", f"先把 {reg} 减少 16")
            value += 16
        if value != 0:
            self._append_instruction(ctx.lines, f"    ADD {reg}, {reg}, #{value}", f"最后把 {reg} 调整 {value}")

    def _emit_global_data(self) -> List[str]:
        lines = ["STACK_TOP .FILL xF000"]
        for name, label in self.globals.items():
            value = self.global_inits[name]
            lines.append(f"{label} .FILL #{value}")
        for value, label in self.string_labels.items():
            chars = [ord(ch) for ch in value] + [0]
            lines.append(f"{label} .FILL #{chars[0]}")
            for ch in chars[1:]:
                lines.append(f"    .FILL #{ch}")
        return lines

    def _emit_literals(self) -> List[str]:
        lines: List[str] = []
        for value, label in self.literal_labels.items():
            lines.append(f"{label} .FILL #{value}")
        return lines
