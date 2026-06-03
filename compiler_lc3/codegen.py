from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from . import ast


class CodegenError(ValueError):
    pass


BUILTINS = {"getchar", "putchar", "puts"}
COMPARE_OPS = {"<", "<=", ">", ">=", "==", "!="}
BARE_INSTRUCTIONS = {"RET", "GETC", "OUT", "PUTS", "HALT"}

# LC-3 opcodes and assembler directives that would conflict with bare function labels
LC3_RESERVED = {
    "ADD", "AND", "NOT", "LD", "LDI", "LDR", "LEA",
    "ST", "STI", "STR", "JMP", "JSR", "JSRR", "RET",
    "RTI", "TRAP", "GETC", "OUT", "PUTS", "IN", "HALT",
    "BR", "BRN", "BRZ", "BRP", "BRNZ", "BRNP", "BRZP", "BRNZP",
    "ORIG", "END", "FILL", "BLKW", "STRINGZ",
}


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
        self.end_label: Optional[str] = None
        self.use_frame_pointer = True
        self.save_r7 = True
        self.saved_regs: List[str] = []
        self.param_base_reg = "R5"
        self.param_offset_base = 2
        self.direct_return_stmt_id: Optional[int] = None
        self.zero_init_locals: Set[str] = set()
        self.beginner_var_labels: Dict[str, str] = {}

    def emit(self, line: str) -> None:
        self.lines.append(line)

    def emit_label(self, label: str) -> None:
        self.lines.append(f"{label}")

    def emit_comment(self, text: str) -> None:
        self.generator._emit_comment(self.lines, text)

    def return_label(self) -> str:
        if self.end_label is None:
            if self.generator.beginner_style:
                self.end_label = self.generator._beginner_label("RETURN")
            else:
                self.end_label = self.generator.new_label(f"{self.func.name}_end")
        return self.end_label

    def alloc_local(self, name: str) -> int:
        if name in self.local_names or name in self.param_names:
            raise CodegenError(f"duplicate local or parameter name: {name}")
        self.local_count += 1
        self.local_names.append(name)
        if self.generator.beginner_style:
            if self.func.name == "main":
                label = name
            else:
                label = f"{self.func.name}_{name}"
            self.beginner_var_labels[name] = label
            self.generator.beginner_vars[(self.func.name, name)] = label
        return -self.local_count

    def lookup(self, name: str):
        if self.generator.beginner_style:
            return self.beginner_var_labels.get(name) or self.var_offsets.get(name)
        return self.var_offsets.get(name)

    def configure_frame(self, *, use_frame_pointer: bool, save_r7: bool, saved_regs: List[str]) -> None:
        self.use_frame_pointer = use_frame_pointer
        self.save_r7 = save_r7
        self.saved_regs = list(saved_regs)
        self.var_offsets = {}
        self.param_base_reg = "R5" if use_frame_pointer else "R6"
        if self.generator.beginner_style:
            for index, param in enumerate(self.param_names):
                if self.func.name == "main":
                    label = param
                else:
                    label = f"{self.func.name}_{param}"
                self.beginner_var_labels[param] = label
                self.generator.beginner_vars[(self.func.name, param)] = label
            return
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
        self.beginner_label_counter = 1
        self.beginner_vars: Dict[str, str] = {}  # (func_name, var_name) -> global label
        self.beginner_storage_labels: List[str] = []
        self._beginner_array_sizes: Dict[tuple, int] = {}  # (func_name, arr_name) -> size

    def generate(self, program: ast.Program) -> str:
        self._collect_globals(program)
        self._collect_functions(program)
        if "main" not in self.functions:
            raise CodegenError("program must define int main()")
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
        self._emit_comment(lines, "entry")
        self._append_instruction(lines, "    LD R6, STACK_TOP", "init SP")
        self._append_instruction(lines, "    AND R5, R5, #0", "clear FP")
        self._append_instruction(lines, f"    JSR {self.function_labels['main']}", "call main")
        self._append_instruction(lines, "    HALT", "halt")
        return lines

    def new_label(self, prefix: str) -> str:
        label = f"{prefix}_{self.label_counter}"
        self.label_counter += 1
        return label

    def _beginner_label(self, prefix: str) -> str:
        label = f"{prefix}_{self.beginner_label_counter}"
        self.beginner_label_counter += 1
        return label

    def _beginner_storage_label(self, prefix: str) -> str:
        label = self._beginner_label(prefix)
        self.beginner_storage_labels.append(label)
        return label

    _CTL_LABEL_MAP = {
        "while_test": "LOOP",
        "while_end": "DONE",
        "for_test": "LOOP",
        "for_step": "NEXT",
        "for_end": "DONE",
        "ifend": "ENDIF",
        "else": "ELSE",
        "not_true": "NOT_TRUE",
        "not_end": "NOT_DONE",
        "cmp_true": "TRUE",
        "cmp_end": "CMP_DONE",
        "sc_false": "FALSE",
        "sc_true": "TRUE",
        "sc_end": "LOGIC_DONE",
        "or_skip": "OR_DONE",
        "and_skip": "AND_DONE",
    }

    def _ctl_label(self, prefix: str) -> str:
        if self.beginner_style:
            mapped = self._CTL_LABEL_MAP.get(prefix, prefix)
            return self._beginner_label(mapped)
        return self.new_label(prefix)

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
        lines = self._merge_duplicate_ands(lines)
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

    def _merge_duplicate_ands(self, lines: List[str]) -> List[str]:
        result: List[str] = []
        last_insn: Optional[str] = None
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith(";"):
                result.append(line)
                continue
            insn = stripped.split(";", 1)[0].strip()
            if insn == "AND R0, R0, #0" and last_insn == "AND R0, R0, #0":
                continue
            result.append(line)
            last_insn = insn
        return result

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
                    if target and not target.startswith("#") and not self._is_register_name(target) and target != "STACK_TOP":
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

    def _is_register_name(self, text: str) -> bool:
        return len(text) == 2 and text[0] == "R" and text[1] in "01234567"

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
        if isinstance(expr, ast.ArrayAccess):
            return f"{self._expr_to_text(expr.array)}[{self._expr_to_text(expr.index)}]"
        if isinstance(expr, ast.ArrayAssign):
            return f"{expr.name}[{self._expr_to_text(expr.index)}] = {self._expr_to_text(expr.value)}"
        if isinstance(expr, ast.Deref):
            return f"*({self._expr_to_text(expr.operand)})"
        if isinstance(expr, ast.AddrOf):
            return f"&{self._expr_to_text(expr.operand)}"
        if isinstance(expr, ast.DerefAssign):
            return f"*({self._expr_to_text(expr.ptr)}) = {self._expr_to_text(expr.value)}"
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

    def _semantic_constant(self, value: int) -> str:
        if 48 <= value <= 57:
            return f"ASCII_{chr(value)}"
        if 65 <= value <= 90:
            return f"ASCII_{chr(value)}"
        if 97 <= value <= 122:
            return f"ASCII_{chr(value)}"
        if value == 10:
            return "NEWLINE"
        if value == 32:
            return "SPACE"
        if value == 0:
            return "ZERO"
        return None

    def literal_label(self, value: int) -> str:
        if value not in self.literal_labels:
            if self.beginner_style:
                name = self._semantic_constant(value)
                if name:
                    self.literal_labels[value] = name
                elif value >= 0:
                    self.literal_labels[value] = f"N_{value}"
                else:
                    self.literal_labels[value] = f"N_NEG_{-value}"
            else:
                self.literal_labels[value] = f"LC_INT_{self.literal_counter}"
            self.literal_counter += 1
        return self.literal_labels[value]

    def string_label(self, value: str) -> str:
        if value not in self.string_labels:
            if self.beginner_style:
                self.string_labels[value] = f"STR{self.string_counter}"
            else:
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
            if self.beginner_style:
                if func.name.upper() in LC3_RESERVED:
                    self.function_labels[func.name] = f"{func.name}_func"
                else:
                    self.function_labels[func.name] = func.name
            else:
                self.function_labels[func.name] = "main" if func.name == "main" else f"FN_{func.name}"

    def _emit_function(self, func: ast.FunctionDef) -> List[str]:
        has_calls = self._block_has_calls(func.body)
        is_main = func.name == "main"
        last_stmt = self._last_executable_stmt(func.body)
        direct_return_stmt_id = id(last_stmt) if isinstance(last_stmt, ast.ReturnStmt) and self._count_returns_in_block(func.body) == 1 else None

        if self.beginner_style:
            return self._emit_function_beginner(func, has_calls, is_main, direct_return_stmt_id)

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
        self._emit_comment(lines, f"int {func.name}(" + ", ".join(f"int {param}" for param in func.params) + ")")
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
            self._append_instruction(lines, "    ADD R6, R6, #-1", f"save {reg}")
            self._append_instruction(lines, f"    STR {reg}, R6, #0", "")
        if self.debug_comments:
            self._emit_function_layout(lines, ctx)
        if ctx.use_frame_pointer:
            for _ in range(ctx.local_count):
                self._append_instruction(lines, "    ADD R6, R6, #-1", "alloc local")
            self._init_locals_zero(ctx)
        self._emit_block(ctx, func.body)
        lines.extend(ctx.lines)
        if ctx.end_label is not None:
            lines.append(f"{ctx.end_label}")
        if ctx.use_frame_pointer:
            for index, reg in enumerate(ctx.saved_regs, start=1):
                self._append_instruction(lines, f"    LDR {reg}, R5, #-{index}", f"restore {reg}")
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

    def _emit_function_beginner(self, func: ast.FunctionDef, has_calls: bool, is_main: bool, direct_return_stmt_id) -> List[str]:
        ctx = FunctionContext(self, func)
        self._collect_locals(ctx, func.body)
        ctx.configure_frame(use_frame_pointer=False, save_r7=False, saved_regs=[])
        ctx.direct_return_stmt_id = direct_return_stmt_id

        lines: List[str] = []
        if not is_main:
            lines.append("")
        lines.append(self.function_labels[func.name])
        self._emit_comment(lines, f"int {func.name}(" + ", ".join(f"int {param}" for param in func.params) + ")")
        save_r7_label = None
        if has_calls and not is_main:
            save_r7_label = self._beginner_storage_label("SAVE_R7")
            self._append_instruction(lines, f"    ST R7, {save_r7_label}", "save R7")
        self._emit_block(ctx, func.body)
        lines.extend(ctx.lines)
        if ctx.end_label is not None:
            lines.append(f"{ctx.end_label}")
        if save_r7_label is not None:
            self._append_instruction(lines, f"    LD R7, {save_r7_label}", "restore R7")
        lines.append("    HALT" if is_main else "    RET")
        return lines

    def _main_is_program_entry(self, is_main: bool) -> bool:
        return self.beginner_style and is_main

    def _emit_function_layout(self, lines: List[str], ctx: FunctionContext) -> None:
        self._emit_comment(lines, "stack frame layout")
        if ctx.use_frame_pointer:
            self._emit_comment(lines, "  [R5 + 0] saved FP")
            if ctx.save_r7:
                self._emit_comment(lines, "  [R5 + 1] saved R7")
            for index, reg in enumerate(ctx.saved_regs, start=1):
                self._emit_comment(lines, f"  [R5 - {index}] saved {reg}")
        elif ctx.save_r7:
            self._emit_comment(lines, "  [R6 + 0] saved R7")
        else:
            self._emit_comment(lines, "  leaf function, no frame")
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
            elif isinstance(item, ast.ArrayDecl):
                if self.beginner_style:
                    base_label = self._beginner_array_label(item.name, 0, ctx.func.name)
                    self._beginner_array_sizes[(ctx.func.name, item.name)] = item.size
                    self.beginner_vars[(ctx.func.name, item.name)] = base_label
                else:
                    ctx.local_count += item.size
                    ctx.local_names.append(item.name)
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
            elif isinstance(item, ast.ArrayDecl):
                if item.init_list is not None and any(self._expr_has_calls(expr) for expr in item.init_list):
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
        if isinstance(expr, ast.ArrayAccess):
            return self._expr_has_calls(expr.array) or self._expr_has_calls(expr.index)
        if isinstance(expr, ast.ArrayAssign):
            return self._expr_has_calls(expr.index) or self._expr_has_calls(expr.value)
        if isinstance(expr, ast.Deref):
            return self._expr_has_calls(expr.operand)
        if isinstance(expr, ast.AddrOf):
            return self._expr_has_calls(expr.operand)
        if isinstance(expr, ast.DerefAssign):
            return self._expr_has_calls(expr.ptr) or self._expr_has_calls(expr.value)
        return False

    def _init_locals_zero(self, ctx: FunctionContext) -> None:
        if not ctx.zero_init_locals:
            return
        self._append_instruction(ctx.lines, "    AND R0, R0, #0", "zero-init locals")
        for name in sorted(ctx.zero_init_locals, key=lambda local_name: ctx.var_offsets[local_name], reverse=True):
            offset = ctx.var_offsets[name]
            self._append_instruction(
                ctx.lines,
                f"    STR R0, R5, #{offset}",
                f"{name} = 0",
            )

    def _emit_store_init(self, ctx: FunctionContext, name: str, expr: ast.Expr) -> None:
        self._emit_expr(ctx, expr)
        self._emit_store_var(ctx, name, "R0")

    def _emit_blank(self, ctx: FunctionContext) -> None:
        if ctx.lines and ctx.lines[-1] != "":
            ctx.lines.append("")

    def _emit_block(self, ctx: FunctionContext, block: ast.Block) -> None:
        had_decls = False
        for item in block.items:
            if isinstance(item, ast.VarDecl):
                type_str = str(item.var_type)
                if item.init is not None:
                    ctx.emit_comment(f"{type_str} {item.name} = {self._expr_to_text(item.init)};")
                    self._emit_store_init(ctx, item.name, item.init)
                else:
                    ctx.emit_comment(f"{type_str} {item.name};")
                    self._append_instruction(ctx.lines, "    AND R0, R0, #0", f"{item.name} = 0")
                    self._emit_store_var(ctx, item.name, "R0")
                had_decls = True
                continue
            if isinstance(item, ast.ArrayDecl):
                coment = f"int {item.name}[{item.size}]"
                if item.init_list:
                    coment += " = {...}"
                ctx.emit_comment(coment + ";")
                if item.init_list:
                    for i, init_expr in enumerate(item.init_list):
                        if i >= item.size:
                            break
                        self._emit_expr(ctx, init_expr)
                        if self.beginner_style:
                            label = self._beginner_array_label(item.name, i, ctx.func.name)
                            self._append_instruction(ctx.lines, f"    ST R0, {label}", f"{item.name}[{i}] = {self._expr_to_text(init_expr)}")
                        else:
                            # Store into stack frame: R5 + base_offset + i
                            # Base offset is tracked in local_names, but we do individual stores
                            offset = ctx.var_offsets.get(item.name)
                            if offset is not None:
                                store_offset = offset + i
                                self._append_instruction(ctx.lines, f"    STR R0, R5, #{store_offset}", f"{item.name}[{i}] = {self._expr_to_text(init_expr)}")
                    if not self.beginner_style and len(item.init_list) < item.size:
                        offset = ctx.var_offsets.get(item.name)
                        if offset is not None:
                            self._append_instruction(ctx.lines, "    AND R0, R0, #0", f"zero remaining {item.name} elements")
                            for i in range(len(item.init_list), item.size):
                                store_offset = offset + i
                                self._append_instruction(ctx.lines, f"    STR R0, R5, #{store_offset}", f"{item.name}[{i}] = 0")
                had_decls = True
                continue
            if had_decls and self.beginner_style:
                self._emit_blank(ctx)
                had_decls = False
            self._emit_stmt(ctx, item)

    def _emit_stmt(self, ctx: FunctionContext, stmt: ast.Statement) -> None:
        if isinstance(stmt, ast.ExprStmt):
            if not isinstance(stmt.expr, ast.Call):
                ctx.emit_comment(self._stmt_to_text(stmt))
            self._emit_expr(ctx, stmt.expr)
            return
        if isinstance(stmt, ast.BlockStmt):
            self._emit_block(ctx, stmt.block)
            return
        if isinstance(stmt, ast.IfStmt):
            if self.beginner_style:
                self._emit_blank(ctx)
            ctx.emit_comment(f"if ({self._expr_to_text(stmt.condition)})")
            if stmt.else_branch is None:
                end_label = self._ctl_label("ifend")
                self._emit_branch_if_false(ctx, stmt.condition, end_label)
                self._emit_stmt(ctx, stmt.then_branch)
                ctx.emit_label(end_label)
                return

            else_label = self._ctl_label("else")
            end_label = self._ctl_label("ifend")
            self._emit_branch_if_false(ctx, stmt.condition, else_label)
            self._emit_stmt(ctx, stmt.then_branch)
            if not self._stmt_always_transfers(stmt.then_branch):
                self._append_instruction(ctx.lines, f"    BRnzp {end_label}", "skip else")
            ctx.emit_label(else_label)
            ctx.emit_comment("else")
            self._emit_stmt(ctx, stmt.else_branch)
            ctx.emit_label(end_label)
            return
        if isinstance(stmt, ast.WhileStmt):
            if self.beginner_style:
                self._emit_blank(ctx)
            test_label = self._ctl_label("while_test")
            end_label = self._ctl_label("while_end")
            ctx.loop_stack.append(LoopLabels(end_label, test_label))
            ctx.emit_comment(f"while ({self._expr_to_text(stmt.condition)})")
            ctx.emit_label(test_label)
            self._emit_branch_if_false(ctx, stmt.condition, end_label)
            self._emit_stmt(ctx, stmt.body)
            self._append_instruction(ctx.lines, f"    BRnzp {test_label}", "loop")
            ctx.emit_label(end_label)
            ctx.loop_stack.pop()
            return
        if isinstance(stmt, ast.ForStmt):
            if self.beginner_style:
                self._emit_blank(ctx)
            test_label = self._ctl_label("for_test")
            has_continue = self._stmt_has_current_loop_continue(stmt.body)
            step_label = self._ctl_label("for_step") if has_continue else None
            end_label = self._ctl_label("for_end")
            init_text = self._expr_to_text(stmt.init) if stmt.init is not None else ""
            cond_text = self._expr_to_text(stmt.condition) if stmt.condition is not None else ""
            step_text = self._expr_to_text(stmt.step) if stmt.step is not None else ""
            ctx.emit_comment(f"for ({init_text}; {cond_text}; {step_text})")
            if stmt.init is not None:
                self._emit_expr(ctx, stmt.init)
            ctx.loop_stack.append(LoopLabels(end_label, step_label or test_label))
            ctx.emit_label(test_label)
            if stmt.condition is not None:
                self._emit_branch_if_false(ctx, stmt.condition, end_label)
            self._emit_stmt(ctx, stmt.body)
            if step_label is not None:
                ctx.emit_label(step_label)
            if stmt.step is not None:
                self._emit_expr(ctx, stmt.step)
            self._append_instruction(ctx.lines, f"    BRnzp {test_label}", "loop")
            ctx.emit_label(end_label)
            ctx.loop_stack.pop()
            return
        if isinstance(stmt, ast.BreakStmt):
            if not ctx.loop_stack:
                raise CodegenError("break used outside loop")
            ctx.emit_comment("break;")
            self._append_instruction(ctx.lines, f"    BRnzp {ctx.loop_stack[-1].break_label}", "break")
            return
        if isinstance(stmt, ast.ContinueStmt):
            if not ctx.loop_stack:
                raise CodegenError("continue used outside loop")
            ctx.emit_comment("continue;")
            self._append_instruction(
                ctx.lines,
                f"    BRnzp {ctx.loop_stack[-1].continue_label}",
                "continue",
            )
            return
        if isinstance(stmt, ast.ReturnStmt):
            ctx.emit_comment(self._stmt_to_text(stmt))
            if stmt.expr is None:
                self._append_instruction(ctx.lines, "    AND R0, R0, #0", "return 0")
            else:
                self._emit_expr(ctx, stmt.expr)
            if ctx.direct_return_stmt_id != id(stmt):
                self._append_instruction(ctx.lines, f"    BRnzp {ctx.return_label()}", "return")
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

    def _stmt_has_current_loop_continue(self, stmt: ast.Statement) -> bool:
        if isinstance(stmt, ast.ContinueStmt):
            return True
        if isinstance(stmt, ast.BlockStmt):
            return any(
                isinstance(item, ast.Statement) and self._stmt_has_current_loop_continue(item)
                for item in stmt.block.items
            )
        if isinstance(stmt, ast.IfStmt):
            return (
                self._stmt_has_current_loop_continue(stmt.then_branch)
                or (stmt.else_branch is not None and self._stmt_has_current_loop_continue(stmt.else_branch))
            )
        if isinstance(stmt, (ast.WhileStmt, ast.ForStmt)):
            return False
        return False

    def _emit_branch_if_false(self, ctx: FunctionContext, expr: ast.Expr, false_label: str) -> None:
        if isinstance(expr, ast.IntLiteral):
            if expr.value == 0:
                self._append_instruction(ctx.lines, f"    BRnzp {false_label}", "always false")
            return
        if isinstance(expr, ast.UnaryOp) and expr.op == "!":
            self._emit_branch_if_true(ctx, expr.operand, false_label)
            return
        # Short-circuit for &&: both must be true, so false if either is false
        if isinstance(expr, ast.BinaryOp) and expr.op == "&&":
            self._emit_branch_if_false(ctx, expr.left, false_label)
            self._emit_branch_if_false(ctx, expr.right, false_label)
            return
        # Short-circuit for ||: false only if both are false
        if isinstance(expr, ast.BinaryOp) and expr.op == "||":
            skip_label = self._ctl_label("or_skip")
            self._emit_branch_if_true(ctx, expr.left, skip_label)
            self._emit_branch_if_false(ctx, expr.right, false_label)
            ctx.emit_label(skip_label)
            return
        if isinstance(expr, ast.BinaryOp) and expr.op in COMPARE_OPS:
            self._emit_compare_branch(ctx, expr, false_label, branch_on_false=True)
            return
        self._emit_expr(ctx, expr)
        self._append_instruction(ctx.lines, "    ADD R0, R0, #0", f"test {self._expr_to_text(expr)}")
        self._append_instruction(ctx.lines, f"    BRz {false_label}", "skip if false")

    def _emit_branch_if_true(self, ctx: FunctionContext, expr: ast.Expr, true_label: str) -> None:
        if isinstance(expr, ast.IntLiteral):
            if expr.value != 0:
                self._append_instruction(ctx.lines, f"    BRnzp {true_label}", "always true")
            return
        if isinstance(expr, ast.UnaryOp) and expr.op == "!":
            self._emit_branch_if_false(ctx, expr.operand, true_label)
            return
        # Short-circuit for ||: true if either is true
        if isinstance(expr, ast.BinaryOp) and expr.op == "||":
            self._emit_branch_if_true(ctx, expr.left, true_label)
            self._emit_branch_if_true(ctx, expr.right, true_label)
            return
        # Short-circuit for &&: true only if both are true
        if isinstance(expr, ast.BinaryOp) and expr.op == "&&":
            skip_label = self._ctl_label("and_skip")
            self._emit_branch_if_false(ctx, expr.left, skip_label)
            self._emit_branch_if_true(ctx, expr.right, true_label)
            ctx.emit_label(skip_label)
            return
        if isinstance(expr, ast.BinaryOp) and expr.op in COMPARE_OPS:
            self._emit_compare_branch(ctx, expr, true_label, branch_on_false=False)
            return
        self._emit_expr(ctx, expr)
        self._append_instruction(ctx.lines, "    ADD R0, R0, #0", f"test {self._expr_to_text(expr)}")
        self._append_instruction(ctx.lines, f"    BRnp {true_label}", "skip if true")

    def _emit_compare_branch(self, ctx: FunctionContext, expr: ast.BinaryOp, label: str, *, branch_on_false: bool) -> None:
        self._emit_expr_into(ctx, expr.left, "R0", ["R1", "R2", "R3", "R4"])
        self._emit_expr_into(ctx, expr.right, "R1", ["R2", "R3", "R4"])
        self._append_instruction(ctx.lines, "    NOT R1, R1", f"R1 = -{self._expr_to_text(expr.right)}")
        self._append_instruction(ctx.lines, "    ADD R1, R1, #1", "")
        self._append_instruction(
            ctx.lines,
            "    ADD R1, R0, R1",
            f"{self._expr_to_text(expr.left)} - {self._expr_to_text(expr.right)}",
        )
        branch = self._compare_branch_opcode(expr.op, branch_on_false=branch_on_false)
        self._append_instruction(ctx.lines, f"    {branch} {label}", self._compare_branch_comment(expr, branch_on_false))

    def _compare_branch_comment(self, expr: ast.BinaryOp, branch_on_false: bool) -> str:
        text = self._expr_to_text(expr)
        if branch_on_false:
            return f"if not ({text}), jump"
        return f"if {text}, jump"

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
        scratch = ["R1", "R2", "R3", "R4", "R5", "R6"] if self.beginner_style else ["R1", "R2", "R3", "R4"]
        self._emit_expr_into(ctx, expr, "R0", scratch)

    def _emit_expr_into(self, ctx: FunctionContext, expr: ast.Expr, target: str, scratch: List[str]) -> None:
        if isinstance(expr, ast.IntLiteral):
            self._emit_load_constant(ctx, target, expr.value)
            return
        if isinstance(expr, ast.StringLiteral):
            label = self.string_label(expr.value)
            self._append_instruction(
                ctx.lines,
                f"    LEA {target}, {label}",
                f"{target} = &{self._expr_to_text(expr)}",
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
                self._append_instruction(ctx.lines, f"    NOT {target}, {target}", f"negate {self._expr_to_text(expr.operand)}")
                self._append_instruction(
                    ctx.lines,
                    f"    ADD {target}, {target}, #1",
                    f"{target} = -({self._expr_to_text(expr.operand)})",
                )
                return
            if expr.op == "!":
                true_label = self._ctl_label("not_true")
                end_label = self._ctl_label("not_end")
                self._append_instruction(
                    ctx.lines,
                    f"    ADD {target}, {target}, #0",
                    f"test {self._expr_to_text(expr.operand)}",
                )
                self._append_instruction(ctx.lines, f"    BRz {true_label}", f"!{self._expr_to_text(expr.operand)}: true")
                self._append_instruction(ctx.lines, f"    AND {target}, {target}, #0", f"{target} = 0 (false)")
                self._append_instruction(ctx.lines, f"    BRnzp {end_label}", "")
                ctx.emit_label(true_label)
                self._append_instruction(ctx.lines, f"    AND {target}, {target}, #0", f"{target} = 1 (true)")
                self._append_instruction(ctx.lines, f"    ADD {target}, {target}, #1", "")
                ctx.emit_label(end_label)
                return
            raise CodegenError(f"unsupported unary operator: {expr.op}")
        if isinstance(expr, ast.BinaryOp):
            if expr.op in ("&&", "||"):
                self._emit_logical_binary(ctx, expr, target, scratch)
            else:
                self._emit_binary(ctx, expr, target, scratch)
            return
        if isinstance(expr, ast.Call):
            self._emit_call(ctx, expr)
            if target != "R0":
                self._append_instruction(ctx.lines, f"    ADD {target}, R0, #0", f"{target} = retval")
            return
        if isinstance(expr, ast.ArrayAccess):
            self._emit_array_access(ctx, expr, target, scratch)
            return
        if isinstance(expr, ast.ArrayAssign):
            self._emit_array_assign(ctx, expr, target, scratch)
            return
        if isinstance(expr, ast.Deref):
            self._emit_deref(ctx, expr, target, scratch)
            return
        if isinstance(expr, ast.AddrOf):
            self._emit_addr_of(ctx, expr, target)
            return
        if isinstance(expr, ast.DerefAssign):
            self._emit_deref_assign(ctx, expr, target, scratch)
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
            self._append_instruction(ctx.lines, f"    ADD {update_reg}, {target}, #0", f"{update_reg} = old {expr.name}")
            self._append_instruction(
                ctx.lines,
                f"    ADD {update_reg}, {update_reg}, #{expr.delta}",
                f"{update_reg} = new {expr.name}",
            )
            self._emit_store_var(ctx, expr.name, update_reg)
            return
        self._append_instruction(
            ctx.lines,
            f"    ADD {target}, {target}, #{expr.delta}",
            f"{target} = {self._expr_to_text(expr)}",
        )
        self._emit_store_var(ctx, expr.name, target)

    def _emit_logical_binary(self, ctx: FunctionContext, expr: ast.BinaryOp, target: str, scratch: List[str]) -> None:
        """Emit short-circuit evaluation for && and ||. Produces 0 or 1 in target."""
        if expr.op == "&&":
            # a && b: if a is false, result=0; otherwise evaluate b as result
            false_label = self._ctl_label("sc_false")
            end_label = self._ctl_label("sc_end")
            self._emit_branch_if_false(ctx, expr.left, false_label)
            self._emit_expr_into(ctx, expr.right, target, scratch)
            self._append_instruction(ctx.lines, f"    ADD {target}, {target}, #0", f"test {self._expr_to_text(expr.right)}")
            self._append_instruction(ctx.lines, f"    BRz {false_label}", "right is false")
            # both true
            self._append_instruction(ctx.lines, f"    AND {target}, {target}, #0", f"{target} = 1 (true)")
            self._append_instruction(ctx.lines, f"    ADD {target}, {target}, #1", "")
            self._append_instruction(ctx.lines, f"    BRnzp {end_label}", "")
            ctx.emit_label(false_label)
            self._append_instruction(ctx.lines, f"    AND {target}, {target}, #0", f"{target} = 0 (false)")
            ctx.emit_label(end_label)
            return

        if expr.op == "||":
            # a || b: if a is true, result=1; otherwise evaluate b as result
            true_label = self._ctl_label("sc_true")
            end_label = self._ctl_label("sc_end")
            self._emit_branch_if_true(ctx, expr.left, true_label)
            self._emit_expr_into(ctx, expr.right, target, scratch)
            self._append_instruction(ctx.lines, f"    ADD {target}, {target}, #0", f"test {self._expr_to_text(expr.right)}")
            self._append_instruction(ctx.lines, f"    BRnp {true_label}", "right is true")
            # both false
            self._append_instruction(ctx.lines, f"    AND {target}, {target}, #0", f"{target} = 0 (false)")
            self._append_instruction(ctx.lines, f"    BRnzp {end_label}", "")
            ctx.emit_label(true_label)
            self._append_instruction(ctx.lines, f"    AND {target}, {target}, #0", f"{target} = 1 (true)")
            self._append_instruction(ctx.lines, f"    ADD {target}, {target}, #1", "")
            ctx.emit_label(end_label)
            return

        raise CodegenError(f"unsupported logical operator: {expr.op}")

    def _emit_binary(self, ctx: FunctionContext, expr: ast.BinaryOp, target: str, scratch: List[str]) -> None:
        if self.beginner_style and self._emit_beginner_binary_immediate(ctx, expr, target, scratch):
            return

        if not scratch:
            self._emit_binary_with_stack_fallback(ctx, expr, target)
            return

        right_reg = scratch[0]
        next_scratch = [reg for reg in scratch[1:] if reg != target]
        self._emit_expr_into(ctx, expr.left, target, scratch)
        # Save left result before evaluating right (right may clobber target).
        save_label = None
        save_left = not (self.beginner_style and self._expr_preserves_other_registers(expr.right))
        if self.beginner_style and save_left:
            save_label = self._beginner_storage_label("LEFT_VALUE")
            self._append_instruction(ctx.lines, f"    ST {target}, {save_label}", f"save {self._expr_to_text(expr.left)}")
        elif not self.beginner_style:
            self._push_reg(ctx, target)
        self._emit_expr_into(ctx, expr.right, right_reg, next_scratch)
        # Restore left result into target
        if self.beginner_style and save_label is not None:
            self._append_instruction(ctx.lines, f"    LD {target}, {save_label}", f"restore {self._expr_to_text(expr.left)}")
        elif not self.beginner_style:
            self._append_instruction(ctx.lines, f"    LDR {target}, R6, #0", f"restore {self._expr_to_text(expr.left)}")
            self._append_instruction(ctx.lines, f"    ADD R6, R6, #1", "")

        if expr.op == "+":
            self._append_instruction(ctx.lines, f"    ADD {target}, {target}, {right_reg}", f"{target} = {self._expr_to_text(expr)}")
            return
        if expr.op == "-":
            self._append_instruction(ctx.lines, f"    NOT {right_reg}, {right_reg}", f"negate {self._expr_to_text(expr.right)}")
            self._append_instruction(ctx.lines, f"    ADD {right_reg}, {right_reg}, #1", "")
            self._append_instruction(ctx.lines, f"    ADD {target}, {target}, {right_reg}", f"{target} = {self._expr_to_text(expr)}")
            return
        if expr.op in ("*", "/", "%"):
            if len(next_scratch) < 3:
                self._emit_binary_with_stack_fallback(ctx, expr, target)
                return
            self._emit_mul_div_mod(ctx, expr, target, right_reg, next_scratch)
            return

        self._append_instruction(ctx.lines, f"    NOT {right_reg}, {right_reg}", f"{self._expr_to_text(expr.left)} - {self._expr_to_text(expr.right)}")
        self._append_instruction(ctx.lines, f"    ADD {right_reg}, {right_reg}, #1", "")
        self._append_instruction(
            ctx.lines,
            f"    ADD {right_reg}, {target}, {right_reg}",
            "",
        )
        true_label = self._ctl_label("cmp_true")
        end_label = self._ctl_label("cmp_end")
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
        self._append_instruction(ctx.lines, f"    {branch} {true_label}", f"{self._expr_to_text(expr)}: true")
        self._append_instruction(ctx.lines, f"    AND {target}, {target}, #0", f"{target} = 0 (false)")
        self._append_instruction(ctx.lines, f"    BRnzp {end_label}", "")
        ctx.emit_label(true_label)
        self._append_instruction(ctx.lines, f"    AND {target}, {target}, #0", f"{target} = 1 (true)")
        self._append_instruction(ctx.lines, f"    ADD {target}, {target}, #1", "")
        ctx.emit_label(end_label)

    def _emit_beginner_binary_immediate(self, ctx: FunctionContext, expr: ast.BinaryOp, target: str, scratch: List[str]) -> bool:
        if not isinstance(expr.right, ast.IntLiteral):
            return False
        if expr.op == "+":
            delta = expr.right.value
        elif expr.op == "-":
            delta = -expr.right.value
        else:
            return False
        if delta < -16 or delta > 15:
            return False

        self._emit_expr_into(ctx, expr.left, target, scratch)
        if delta != 0:
            self._append_instruction(ctx.lines, f"    ADD {target}, {target}, #{delta}", f"{target} = {self._expr_to_text(expr)}")
        return True

    def _expr_preserves_other_registers(self, expr: ast.Expr) -> bool:
        if isinstance(expr, (ast.IntLiteral, ast.StringLiteral, ast.Variable)):
            return True
        if isinstance(expr, ast.AddrOf) and isinstance(expr.operand, ast.Variable):
            return True
        return False

    def _emit_mul_div_mod(self, ctx: FunctionContext, expr: ast.BinaryOp, target: str,
                          right_reg: str, scratch: List[str]) -> None:
        """Emit software multiply, divide, or modulo. Uses 3 scratch regs beyond target+right_reg."""
        acc = scratch[0]        # accumulator: product, quotient, or remainder
        counter = scratch[1]    # counter (|left| for mul) or dividend (|left| for div/mod)
        sign_reg = scratch[2]   # sign flag: 0=positive result, 1=negative result

        # --- sign handling: make both operands positive, track sign ---
        self._append_instruction(ctx.lines, f"    AND {sign_reg}, {sign_reg}, #0", "sign flag = 0")
        self._append_instruction(ctx.lines, f"    ADD {counter}, {target}, #0", f"{counter} = |left| (copy)")

        # make left positive
        mul_left_ok = self.new_label("mul_left_ok")
        self._append_instruction(ctx.lines, f"    ADD {target}, {target}, #0")
        self._append_instruction(ctx.lines, f"    BRzp {mul_left_ok}")
        self._append_instruction(ctx.lines, f"    NOT {target}, {target}")
        self._append_instruction(ctx.lines, f"    ADD {target}, {target}, #1")
        self._append_instruction(ctx.lines, f"    ADD {sign_reg}, {sign_reg}, #1", "toggle sign")
        ctx.emit_label(mul_left_ok)

        # make right positive
        mul_right_ok = self.new_label("mul_right_ok")
        self._append_instruction(ctx.lines, f"    ADD {right_reg}, {right_reg}, #0")
        self._append_instruction(ctx.lines, f"    BRzp {mul_right_ok}")
        self._append_instruction(ctx.lines, f"    NOT {right_reg}, {right_reg}")
        self._append_instruction(ctx.lines, f"    ADD {right_reg}, {right_reg}, #1")
        self._append_instruction(ctx.lines, f"    ADD {sign_reg}, {sign_reg}, #1", "toggle sign")
        ctx.emit_label(mul_right_ok)

        # --- dispatch on operator ---
        if expr.op == "*":
            self._emit_mul(ctx, target, right_reg, acc, counter, sign_reg)
        else:
            self._emit_div_mod(ctx, expr.op == "%", target, right_reg, acc, counter, sign_reg)

    def _emit_mul(self, ctx: FunctionContext, left: str, right: str,
                  acc: str, counter: str, sign_reg: str) -> None:
        """|left| * |right| via repeated addition; |left| is in `counter` (copy of |left|)."""
        self._append_instruction(ctx.lines, f"    AND {acc}, {acc}, #0", "acc = 0")
        mul_loop = self.new_label("mul_loop")
        mul_done = self.new_label("mul_done")
        self._append_instruction(ctx.lines, f"    ADD {counter}, {left}, #0", "counter = |left|")
        self._append_instruction(ctx.lines, f"    BRz {mul_done}")
        ctx.emit_label(mul_loop)
        self._append_instruction(ctx.lines, f"    ADD {acc}, {acc}, {right}", "acc += |right|")
        self._append_instruction(ctx.lines, f"    ADD {counter}, {counter}, #-1")
        self._append_instruction(ctx.lines, f"    BRp {mul_loop}")
        ctx.emit_label(mul_done)
        self._emit_apply_sign(ctx, acc, sign_reg, left)  # result back in left

    def _emit_div_mod(self, ctx: FunctionContext, want_remainder: bool,
                      left: str, right: str, acc: str, counter: str, sign_reg: str) -> None:
        """|left| / |right| or |left| % |right| via repeated subtraction.

        At entry: left=|left|, right=|right|, sign_reg=toggle-count,
                  counter=stale copy (from before abs), acc=unused.

        Strategy: save sign LSB into `left` (R0) because it's free during
        the division loop.  First copy |left| to `counter` (dividend), then
        overwrite `left` with sign flag.  After the loop, apply sign to
        result and put it back in `left`."""
        # 1. Copy |left| -> counter (dividend)
        self._append_instruction(ctx.lines, f"    ADD {counter}, {left}, #0", "dividend = |left|")
        # 2. Extract sign LSB and save in left (R0, now free)
        self._append_instruction(ctx.lines, f"    AND {sign_reg}, {sign_reg}, #1", "sign = LSB")
        self._append_instruction(ctx.lines, f"    ADD {left}, {sign_reg}, #0", "save sign in R0")
        # Now: R0=sign(0|1), R1=divisor, R2=free, R3=dividend, R4=free(for temp)
        # 3. Zero acc (quotient).  sign_reg is freed for loop temp.
        self._append_instruction(ctx.lines, f"    AND {acc}, {acc}, #0", "quotient = 0")

        # 4. Division by zero guard
        div_loop = self.new_label("div_loop")
        div_done = self.new_label("div_done")
        self._append_instruction(ctx.lines, f"    ADD {right}, {right}, #0")
        self._append_instruction(ctx.lines, f"    BRz {div_done}", "div by zero -> 0")

        # 5. Repeated subtraction loop (sign_reg = R4 = temp)
        ctx.emit_label(div_loop)
        self._append_instruction(ctx.lines, f"    NOT {sign_reg}, {right}")
        self._append_instruction(ctx.lines, f"    ADD {sign_reg}, {sign_reg}, #1")
        self._append_instruction(ctx.lines, f"    ADD {sign_reg}, {counter}, {sign_reg}", "dividend - divisor")
        self._append_instruction(ctx.lines, f"    BRn {div_done}")
        self._append_instruction(ctx.lines, f"    ADD {counter}, {sign_reg}, #0", "dividend -= divisor")
        self._append_instruction(ctx.lines, f"    ADD {acc}, {acc}, #1", "quotient++")
        self._append_instruction(ctx.lines, f"    BRnzp {div_loop}")
        ctx.emit_label(div_done)

        # 6. Result: quotient in acc(R2), remainder in counter(R3), sign in left(R0)
        result_reg = counter if want_remainder else acc
        sign_ok = self.new_label("sign_ok")
        self._append_instruction(ctx.lines, f"    ADD {left}, {left}, #0", "test sign")  # left still holds sign
        self._append_instruction(ctx.lines, f"    BRz {sign_ok}")
        self._append_instruction(ctx.lines, f"    NOT {result_reg}, {result_reg}")
        self._append_instruction(ctx.lines, f"    ADD {result_reg}, {result_reg}, #1")
        ctx.emit_label(sign_ok)
        self._append_instruction(ctx.lines, f"    ADD {left}, {result_reg}, #0", "R0 = result")

    def _emit_apply_sign(self, ctx: FunctionContext, acc: str, sign_reg: str, target: str) -> None:
        """Apply sign to acc: if sign_reg LSB is 1, negate acc. Result in target."""
        self._append_instruction(ctx.lines, f"    AND {sign_reg}, {sign_reg}, #1", "sign = LSB")
        self._append_instruction(ctx.lines, f"    ADD {target}, {acc}, #0")
        sign_end = self.new_label("sign_end")
        self._append_instruction(ctx.lines, f"    ADD {sign_reg}, {sign_reg}, #0")
        self._append_instruction(ctx.lines, f"    BRz {sign_end}")
        self._append_instruction(ctx.lines, f"    NOT {target}, {target}")
        self._append_instruction(ctx.lines, f"    ADD {target}, {target}, #1")
        ctx.emit_label(sign_end)

    def _emit_binary_with_stack_fallback(self, ctx: FunctionContext, expr: ast.BinaryOp, target: str) -> None:
        ctx.emit_comment("(spill to stack)")
        self._emit_expr_into(ctx, expr.left, target, [])
        self._push_reg(ctx, target)
        self._emit_expr_into(ctx, expr.right, target, [])
        self._append_instruction(ctx.lines, "    ADD R6, R6, #-1", "")
        self._append_instruction(ctx.lines, f"    STR {target}, R6, #0", "")
        temp_reg = "R1" if target != "R1" else "R2"
        self._append_instruction(ctx.lines, f"    LDR {temp_reg}, R6, #1", f"{temp_reg} = {self._expr_to_text(expr.left)}")
        self._append_instruction(ctx.lines, f"    LDR {target}, R6, #0", f"{target} = {self._expr_to_text(expr.right)}")
        self._append_instruction(ctx.lines, "    ADD R6, R6, #2", "")

        if expr.op == "+":
            self._append_instruction(ctx.lines, f"    ADD {target}, {temp_reg}, {target}", f"{target} = {self._expr_to_text(expr)}")
            return
        if expr.op == "-":
            self._append_instruction(ctx.lines, f"    NOT {target}, {target}", f"negate {self._expr_to_text(expr.right)}")
            self._append_instruction(ctx.lines, f"    ADD {target}, {target}, #1", "")
            self._append_instruction(ctx.lines, f"    ADD {target}, {temp_reg}, {target}", f"{target} = {self._expr_to_text(expr)}")
            return

        # mul/div/mod: rearrange operands for _emit_mul_div_mod.
        # Currently temp_reg=left, target=right. Need: target=left, right_reg=right.
        if expr.op in ("*", "/", "%"):
            self._append_instruction(ctx.lines, "    ADD R6, R6, #-1", "")
            self._append_instruction(ctx.lines, f"    STR {target}, R6, #0", "save right to stack")
            self._append_instruction(ctx.lines, f"    ADD {target}, {temp_reg}, #0", "target = left")
            right_reg = "R2" if temp_reg != "R2" else "R3"
            self._append_instruction(ctx.lines, f"    LDR {right_reg}, R6, #0", "right_reg = right")
            self._append_instruction(ctx.lines, "    ADD R6, R6, #1", "pop right")
            # Build scratch from registers not used by target or right_reg.
            all_regs = ["R0", "R1", "R2", "R3", "R4"]
            scratch_regs = [r for r in all_regs if r != target and r != right_reg][:3]
            self._emit_mul_div_mod(ctx, expr, target, right_reg, scratch_regs)
            return

        self._append_instruction(ctx.lines, f"    NOT {target}, {target}", f"{self._expr_to_text(expr.left)} - {self._expr_to_text(expr.right)}")
        self._append_instruction(ctx.lines, f"    ADD {target}, {target}, #1", "")
        self._append_instruction(
            ctx.lines,
            f"    ADD {target}, {temp_reg}, {target}",
            "",
        )
        true_label = self._ctl_label("cmp_true")
        end_label = self._ctl_label("cmp_end")
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
        self._append_instruction(ctx.lines, f"    {branch} {true_label}", f"{self._expr_to_text(expr)}: true")
        self._append_instruction(ctx.lines, f"    AND {target}, {target}, #0", f"{target} = 0 (false)")
        self._append_instruction(ctx.lines, f"    BRnzp {end_label}", "")
        ctx.emit_label(true_label)
        self._append_instruction(ctx.lines, f"    AND {target}, {target}, #0", f"{target} = 1 (true)")
        self._append_instruction(ctx.lines, f"    ADD {target}, {target}, #1", "")
        ctx.emit_label(end_label)

    def _emit_call(self, ctx: FunctionContext, call: ast.Call) -> None:
        ctx.emit_comment(self._expr_to_text(call))
        if call.name in BUILTINS:
            if call.name == "getchar":
                if call.args:
                    raise CodegenError("getchar takes no arguments")
                self._append_instruction(ctx.lines, "    GETC", "read char")
            elif call.name in {"putchar", "puts"}:
                if len(call.args) != 1:
                    raise CodegenError(f"{call.name} takes exactly one argument")
                self._emit_expr(ctx, call.args[0])
                if call.name == "putchar":
                    self._append_instruction(ctx.lines, "    OUT", "print char")
                else:
                    self._append_instruction(ctx.lines, "    PUTS", "print string")
                if not self.beginner_style:
                    self._append_instruction(ctx.lines, "    AND R0, R0, #0", f"{call.name} ret = 0")
            else:
                raise CodegenError(f"unsupported builtin: {call.name}")
            return
        if self.beginner_style:
            callee_func = self.functions.get(call.name)
            if callee_func is None:
                raise CodegenError(f"undefined function: {call.name}")
            for i, arg in enumerate(call.args):
                self._emit_expr(ctx, arg)
                param_name = callee_func.params[i]
                if call.name == "main":
                    param_label = param_name
                else:
                    param_label = f"{call.name}_{param_name}"
                self._append_instruction(ctx.lines, f"    ST R0, {param_label}", f"arg: {param_name}")
            self._append_instruction(ctx.lines, f"    JSR {self.function_labels[call.name]}", call.name)
        else:
            for arg in reversed(call.args):
                self._emit_expr(ctx, arg)
                self._push_reg(ctx, "R0")
            if call.name not in self.functions:
                raise CodegenError(f"undefined function: {call.name}")
            target = self.function_labels[call.name]
            self._append_instruction(ctx.lines, f"    JSR {target}", call.name)
            if call.args:
                self._emit_add_imm(ctx, "R6", len(call.args))

    # ── array / pointer codegen ──────────────────────────────────────────

    def _emit_array_access(self, ctx: FunctionContext, expr: ast.ArrayAccess,
                           target: str, scratch: List[str]) -> None:
        """Load arr[index] into target via base+index, then LDR."""
        if not isinstance(expr.array, ast.Variable):
            raise CodegenError("array access requires a named array variable")
        name = expr.array.name

        addr_reg = scratch[0] if scratch and scratch[0] != target else (scratch[1] if len(scratch) > 1 else self._pick_address_reg(target))
        self._emit_expr_into(ctx, expr.index, target, scratch)
        self._emit_array_base_addr(ctx, name, addr_reg)
        self._append_instruction(ctx.lines, f"    ADD {addr_reg}, {addr_reg}, {target}")
        self._append_instruction(ctx.lines, f"    LDR {target}, {addr_reg}, #0", f"{target} = {name}[{self._expr_to_text(expr.index)}]")

    def _emit_array_assign(self, ctx: FunctionContext, expr: ast.ArrayAssign,
                           target: str, scratch: List[str]) -> None:
        """Store value into arr[index] via base+index, then STR.

        Index is computed first (with full scratch including target) so that
        mul/div/mod inside the index expression doesn't clobber the value
        register.  The index is saved across the value computation."""
        # Pick an index register distinct from the eventual value target.
        idx_reg = scratch[0] if scratch and scratch[0] != target else (scratch[1] if len(scratch) > 1 else self._pick_address_reg(target))
        # Compute index first — full scratch pool (including target, which is
        # free because we haven't computed the value yet).
        all_regs = [r for r in ["R0", "R1", "R2", "R3", "R4", "R5", "R6"]
                    if r != idx_reg]
        self._emit_expr_into(ctx, expr.index, idx_reg, all_regs)
        # Save index across value computation.
        if self.beginner_style:
            save_label = self._beginner_storage_label("ARRAY_INDEX")
            self._append_instruction(ctx.lines, f"    ST {idx_reg}, {save_label}", f"save index ({self._expr_to_text(expr.index)})")
        else:
            self._push_reg(ctx, idx_reg)
        # Compute value into target.
        self._emit_expr_into(ctx, expr.value, target, scratch)
        val_reg = target
        # Restore index.
        if self.beginner_style:
            self._append_instruction(ctx.lines, f"    LD {idx_reg}, {save_label}", f"restore index")
        else:
            self._append_instruction(ctx.lines, f"    LDR {idx_reg}, R6, #0", "restore index")
            self._append_instruction(ctx.lines, "    ADD R6, R6, #1", "")
        addr_reg = scratch[0] if scratch and scratch[0] not in (val_reg, idx_reg) else (scratch[1] if len(scratch) > 1 and scratch[1] not in (val_reg, idx_reg) else self._pick_address_reg(val_reg, idx_reg))
        self._emit_array_base_addr(ctx, expr.name, addr_reg)
        self._append_instruction(ctx.lines, f"    ADD {addr_reg}, {addr_reg}, {idx_reg}")
        self._append_instruction(ctx.lines, f"    STR {val_reg}, {addr_reg}, #0", f"{expr.name}[{self._expr_to_text(expr.index)}] = {self._expr_to_text(expr.value)}")

    def _emit_array_base_addr(self, ctx: FunctionContext, name: str, addr_reg: str) -> None:
        """Compute the base address of an array into addr_reg."""
        # Check beginner mode first
        if self.beginner_style:
            beg_key = (ctx.func.name, name)
            base_label = self.beginner_vars.get(beg_key)
            if base_label is not None:
                self._append_instruction(ctx.lines, f"    LEA {addr_reg}, {base_label}")
                return
            raise CodegenError(f"undefined beginner array: {name}")
        result = ctx.lookup(name)
        if result is not None:
            # Default mode: R5 + offset
            offset = result
            if -16 <= offset <= 15:
                self._append_instruction(ctx.lines, f"    ADD {addr_reg}, R5, #{offset}")
            else:
                self._emit_load_constant(ctx, addr_reg, offset)
                self._append_instruction(ctx.lines, f"    ADD {addr_reg}, R5, {addr_reg}")
            return
        if name in self.globals:
            self._append_instruction(ctx.lines, f"    LEA {addr_reg}, {self.globals[name]}")
            return
        raise CodegenError(f"undefined array: {name}")

    def _beginner_array_label(self, name: str, index: int, func_name: str) -> str:
        """Generate a global label for a beginner-mode array element."""
        if func_name == "main":
            return f"{name}_{index}"
        return f"{func_name}_{name}_{index}"

    def _emit_deref(self, ctx: FunctionContext, expr: ast.Deref,
                    target: str, scratch: List[str]) -> None:
        """Load *ptr: evaluate ptr, then LDR through it."""
        self._emit_expr_into(ctx, expr.operand, target, scratch)
        self._append_instruction(ctx.lines, f"    LDR {target}, {target}, #0", f"{target} = *ptr")

    def _emit_addr_of(self, ctx: FunctionContext, expr: ast.AddrOf, target: str) -> None:
        """Take address of &var or &arr[i]."""
        inner = expr.operand
        if isinstance(inner, ast.Variable):
            result = ctx.lookup(inner.name)
            if result is not None:
                if isinstance(result, str):
                    # Beginner mode: LEA to global label
                    self._append_instruction(ctx.lines, f"    LEA {target}, {result}", f"{target} = &{inner.name}")
                    return
                # Default mode local: R5 + offset
                offset = result
                if -16 <= offset <= 15:
                    self._append_instruction(ctx.lines, f"    ADD {target}, R5, #{offset}", f"{target} = &{inner.name}")
                else:
                    self._emit_load_constant(ctx, target, offset)
                    self._append_instruction(ctx.lines, f"    ADD {target}, R5, {target}")
                return
            if inner.name in self.globals:
                self._append_instruction(ctx.lines, f"    LEA {target}, {self.globals[inner.name]}", f"{target} = &{inner.name}")
                return
            raise CodegenError(f"undefined variable: {inner.name}")
        if isinstance(inner, ast.ArrayAccess) and isinstance(inner.array, ast.Variable):
            # &arr[i]: compute base + index
            self._emit_array_base_addr(ctx, inner.array.name, target)
            idx_reg = "R1"
            self._emit_expr_into(ctx, inner.index, idx_reg, ["R2", "R3", "R4"])
            self._append_instruction(ctx.lines, f"    ADD {target}, {target}, {idx_reg}")
            return
        raise CodegenError(f"cannot take address of this expression")

    def _emit_deref_assign(self, ctx: FunctionContext, expr: ast.DerefAssign,
                           target: str, scratch: List[str]) -> None:
        """Store value through pointer: *ptr = value."""
        self._emit_expr_into(ctx, expr.value, target, scratch)
        ptr_reg = scratch[0] if scratch and scratch[0] != target else (
            scratch[1] if len(scratch) > 1 else self._pick_address_reg(target))
        self._emit_expr_into(ctx, expr.ptr, ptr_reg, [r for r in scratch if r != ptr_reg])
        self._append_instruction(ctx.lines, f"    STR {target}, {ptr_reg}, #0", f"*ptr = {self._expr_to_text(expr.value)}")

    # ── helpers ──────────────────────────────────────────────────────────

    def _push_reg(self, ctx: FunctionContext, reg: str) -> None:
        self._append_instruction(ctx.lines, "    ADD R6, R6, #-1", f"push {reg}")
        self._append_instruction(ctx.lines, f"    STR {reg}, R6, #0", "")

    def _pick_address_reg(self, *reserved: str) -> str:
        for reg in ("R4", "R3", "R2", "R1", "R0"):
            if reg not in reserved:
                return reg
        raise CodegenError("no register available for address calculation")

    def _emit_load_var(self, ctx: FunctionContext, name: str, target: str) -> None:
        result = ctx.lookup(name)
        if result is not None:
            if isinstance(result, str):
                self._append_instruction(
                    ctx.lines,
                    f"    LD {target}, {result}",
                    f"{target} = {name}",
                )
                return
            base_reg = ctx.param_base_reg if name in ctx.param_names else "R5"
            self._append_instruction(
                ctx.lines,
                f"    LDR {target}, {base_reg}, #{result}",
                f"{target} = {name}",
            )
            return
        if name in self.globals:
            if self.beginner_style:
                self._append_instruction(ctx.lines, f"    LD {target}, {self.globals[name]}", f"{target} = {name}")
            else:
                addr_reg = self._pick_address_reg(target)
                self._append_instruction(ctx.lines, f"    LEA {addr_reg}, {self.globals[name]}", "")
                self._append_instruction(ctx.lines, f"    LDR {target}, {addr_reg}, #0", f"{target} = {name} (global)")
            return
        raise CodegenError(f"undefined variable: {name}")

    def _emit_store_var(self, ctx: FunctionContext, name: str, source: str) -> None:
        result = ctx.lookup(name)
        if result is not None:
            if isinstance(result, str):
                self._append_instruction(
                    ctx.lines,
                    f"    ST {source}, {result}",
                    f"{name} = {source}",
                )
                return
            base_reg = ctx.param_base_reg if name in ctx.param_names else "R5"
            self._append_instruction(
                ctx.lines,
                f"    STR {source}, {base_reg}, #{result}",
                f"{name} = {source}",
            )
            return
        if name in self.globals:
            if self.beginner_style:
                self._append_instruction(ctx.lines, f"    ST {source}, {self.globals[name]}", f"{name} = {source}")
            else:
                addr_reg = self._pick_address_reg(source)
                self._append_instruction(ctx.lines, f"    LEA {addr_reg}, {self.globals[name]}", "")
                self._append_instruction(ctx.lines, f"    STR {source}, {addr_reg}, #0", f"{name} = {source} (global)")
            return
        raise CodegenError(f"undefined variable: {name}")

    def _emit_load_constant(self, ctx: FunctionContext, reg: str, value: int) -> None:
        if -16 <= value <= 15:
            if value == 0:
                self._append_instruction(ctx.lines, f"    AND {reg}, {reg}, #0", f"{reg} = 0")
            else:
                self._append_instruction(ctx.lines, f"    AND {reg}, {reg}, #0", "")
                self._append_instruction(ctx.lines, f"    ADD {reg}, {reg}, #{value}", f"{reg} = {value}")
            return
        self._append_instruction(ctx.lines, f"    LD {reg}, {self.literal_label(value)}", f"{reg} = {value}")

    def _emit_add_imm(self, ctx: FunctionContext, reg: str, value: int) -> None:
        while value > 15:
            self._append_instruction(ctx.lines, f"    ADD {reg}, {reg}, #15", "")
            value -= 15
        while value < -16:
            self._append_instruction(ctx.lines, f"    ADD {reg}, {reg}, #-16", "")
            value += 16
        if value != 0:
            self._append_instruction(ctx.lines, f"    ADD {reg}, {reg}, #{value}", "")

    def _emit_global_data(self) -> List[str]:
        lines: List[str] = []
        if self.beginner_style:
            lines.append("")
        if not self.beginner_style:
            lines.append("STACK_TOP .FILL xF000")
        for name, label in self.globals.items():
            value = self.global_inits[name]
            lines.append(f"{label} .FILL #{value}")
        if self.beginner_style:
            for (func_name, var_name), label in sorted(self.beginner_vars.items()):
                arr_size = self._beginner_array_sizes.get((func_name, var_name))
                if arr_size and arr_size > 1:
                    # Array: emit consecutive labels arr_0, arr_1, ... arr_N-1
                    for i in range(arr_size):
                        elem_label = self._beginner_array_label(var_name, i, func_name)
                        lines.append(f"{elem_label} .FILL #0")
                else:
                    lines.append(f"{label} .FILL #0")
            for label in self.beginner_storage_labels:
                lines.append(f"{label} .FILL #0")
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
