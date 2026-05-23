# compiler-lc3

一个将 C 语言子集编译为 LC-3 汇编的教学型编译器项目。

## 项目简介

本项目实现了一条简化的编译流程：

1. `lexer.py` 负责词法分析
2. `parser.py` 负责递归下降语法分析
3. `ast.py` 定义抽象语法树
4. `optimizer.py` 执行简单常量折叠和语句裁剪
5. `codegen.py` 生成 LC-3 汇编代码
6. `__main__.py` 提供命令行入口

项目目标是清晰、可读、便于实验，不追求完整 C 兼容。

## 当前支持

- 全局和局部 `int` 变量
- 带 `int` 参数和 `int` 返回值的函数
- `if` / `else if` / `else`
- `while`、`for`
- `break`、`continue`、`return`
- 表达式：`+`、`-`、`!`、`<`、`<=`、`>`、`>=`、`==`、`!=`
- 内建函数：`getchar()`、`putchar(int)`、`puts(char*)`
- 作为 `puts` 参数的字符串字面量

不支持完整 C 语法和标准库。更详细的说明见 [lc3说明书.md](/home/lbh/projects/compiler-lc3/lc3说明书.md)。

## 目录结构

- `compiler_lc3/`：编译器主体
- `tests/cases/`：端到端测试用例
- `tests/run_tests.py`：测试入口，负责编译、汇编和仿真校验
- `examples/`：示例输入程序
- `build/`：手动编译输出目录
- `lc3tools/`：仓库内置的 LC-3 工具链

## 使用方法

将 C 源文件编译为 LC-3 汇编：

```bash
python3 -m compiler_lc3 examples/sum.c -o build/sum.asm
```

生成带调试注释的汇编：

```bash
python3 -m compiler_lc3 tests/cases/for_and_call.c -o tests/build/for_and_call.asm -d
```

如果省略 `-o`，输出文件默认与输入文件同名，仅扩展名改为 `.asm`。

## 构建 LC-3 工具链

测试依赖仓库自带的 `lc3tools`：

```bash
cd lc3tools
./configure --installdir "$PWD/install"
make
make install
```

## 运行测试

执行端到端回归测试：

```bash
python3 tests/run_tests.py
```

该测试会自动：

- 调用 `compiler_lc3` 生成汇编
- 使用 `lc3as` 汇编为目标文件
- 启动 `lc3sim` 运行程序
- 校验全局变量结果、程序输出和调试注释

## 开发说明

- 编译入口在 `compiler_lc3/__main__.py`
- 新增语法时通常需要同时修改 `lexer.py`、`parser.py`、`ast.py` 和 `codegen.py`
- 新功能建议在 `tests/cases/` 中补充对应 `.c` 用例，并在 `tests/run_tests.py` 中注册

这个项目更适合作为课程实验、编译原理练习和 LC-3 代码生成参考。
