# compiler-lc3

一个将小型 C 子集编译为 LC-3 汇编的教学型编译器。

项目目标不是完整兼容 C，而是提供一条清晰、可测试、适合课程实验的编译链，并特别支持一种接近强学生手写 LC-3 的输出模式。

## 编译流程

```text
lexer.py -> parser.py -> optimizer.py -> codegen.py -> LC-3 assembly
```

- `lexer.py`：词法分析，支持注释、字符串和当前语言子集的运算符。
- `parser.py`：递归下降语法分析。
- `ast.py`：抽象语法树节点。
- `optimizer.py`：常量折叠、简单死分支消除和安全的短路逻辑优化。
- `codegen.py`：生成默认编译器风格或手写者风格 LC-3。
- `__main__.py`：命令行入口。

## 当前支持的语言特性

### 类型和声明

- 标量类型：`int`、`char`、`bool`，均按 LC-3 16 位 word 存储。
- 指针声明：`int* p;`、`int** pp;` 等基础形式。
- 全局变量：`int g;`、`int g = 5;`，初始化值必须是数字常量。
- 局部变量：`int x;`、`char c = 65;`、`bool ok = expr;`。
- 局部数组：`int a[4];`、`int a[4] = {1, 2, 3, 4};`。
- 嵌套块内局部声明。

### 表达式和运算符

| 类别 | 运算符 / 形式 |
|------|---------------|
| 赋值 | `=` `+=` `-=` `*=` `/=` `%=` |
| 算术 | `+` `-` `*` `/` `%` |
| 比较 | `<` `<=` `>` `>=` `==` `!=` |
| 逻辑 | `!` `&&` `||`，支持短路求值 |
| 自增自减 | `++x` `--x` `x++` `x--` |
| 指针 | `&x` `&arr[i]` `*p` `*p = value` |
| 数组 | `arr[i]` `arr[i] = value` |
| 函数调用 | `func(a, b + 1)` |

整数除法和取模按 C 的向零截断语义实现。除零目前生成 0，属于教学简化行为。

### 控制流和函数

- `if` / `else` / `else if`
- `while`
- `for (init; cond; step)`，三段均可省略
- `break` / `continue`
- `return expr;` / `return;`
- 多参数函数调用，当前测试覆盖到 5 个参数
- 基础递归和调用链

### 字面量、注释和内建函数

- 十进制整数：`42`
- 字符串：`"hello\n"`，用于 `puts`
- 字符串转义：`\n` `\t` `\"` `\\`
- 单行注释：`//`
- 块注释：`/* ... */`

| 函数 | LC-3 指令 | 说明 |
|------|-----------|------|
| `getchar()` | `GETC` | 读入一个字符，返回 ASCII 值 |
| `putchar(int)` | `OUT` | 输出一个字符，返回 0 |
| `puts(char*)` | `PUTS` | 输出字符串，返回 0 |

## 输出模式

### 默认模式

默认模式生成标准编译器风格 LC-3：

- 使用 `R5` 作为帧指针。
- 使用 `R6` 作为栈指针。
- 函数参数压栈传递。
- 函数内部按需要保存/恢复寄存器。
- `main` 由启动桩调用，程序最终 `HALT`。

```bash
python3 -m compiler_lc3 examples/sum.c -o build/sum.asm
```

### 手写者风格：`--beginner-style`

`--beginner-style` 更准确地说是“手写者风格”：生成的 LC-3 应该像一个写得扎实的学生手工翻译出来的代码，而不是机械编译器输出。

这个模式的原则：

- `.ORIG x3000` 后直接进入 `main`，没有启动桩。
- 不使用 `R5/R6` 栈帧。
- 普通变量和参数用具名 `.FILL` 标签保存，通过 `LD` / `ST` 访问。
- 函数调用用具名参数标签传参。
- `main` 中调用函数不保存无用的入口 `R7`，因为最终直接 `HALT`。
- 非 `main` 函数如果会继续调用其他函数，则在函数入口保存一次 `R7`，返回前恢复。
- 简单表达式尽量生成自然手写形式，例如 `LD R0, x`、`LD R1, y`、`ADD R0, R0, R1`。
- 函数、代码区和数据区之间保留清晰空行。

```bash
python3 -m compiler_lc3 tests/cases/for_and_call_output.c -o build/for_and_call_output.asm --beginner-style
```

### 调试注释：`-d`

`-d` / `--debug-comments` 会加入源码级和 LC-3 步骤级注释。

```bash
python3 -m compiler_lc3 tests/cases/for_and_call_output.c -o build/for_and_call_output.asm -d
python3 -m compiler_lc3 tests/cases/for_and_call_output.c -o build/for_and_call_output.asm -d --beginner-style
```

在 `-d --beginner-style` 下，注释也按教学可读性生成。例如条件跳转会说明跳转含义：

```asm
BRzp DONE_3          ; if not (i < n), jump
```

## 仍不支持的 C 特性

当前只支持项目测试覆盖的 C 子集。以下特性不支持或不保证完整 C 语义：

- 预处理器：`#include`、`#define`
- `void`、`long`、`short`、`unsigned`、`struct`、`enum`、`typedef`
- 字符字面量：`'A'`
- 十六进制、八进制、浮点字面量
- 多变量声明：`int a, b;`
- 全局数组
- 函数原型声明
- `for (int i = 0; ...)`
- `switch/case`、`do while`、`goto`
- 三目运算符、逗号运算符、`sizeof`、类型转换
- 位运算：`|` `^` `~` `<<` `>>`
- 多维数组、数组参数、完整指针算术、完整类型检查
- 完整递归语义在 `--beginner-style` 下不作为目标，因为该模式使用具名全局标签保存参数和局部值。

## 测试

### 本地完整测试

本地测试会做三类验证：

1. 编译所有用例，并与 `tests/golden/` 中提交的汇编逐行对比。
2. 调用 `lc3as` 汇编，并用 `lc3sim` 真实执行检查输出和全局变量。
3. 用 `gcc` 编译同一份 C 用例生成本机 ELF，再把 GCC 的实际运行结果与 LC-3 仿真的实际运行结果直接对拍。

```bash
python3 tests/run_tests.py
```

也可以只运行 GCC oracle：

```bash
python3 tests/oracle.py
python3 tests/oracle.py tests/cases/array_loop.c
```

本地完整测试依赖仓库内的 `lc3tools/` 和系统 `gcc`。如果需要重新构建 LC-3 工具链：

```bash
cd lc3tools
./configure --installdir "$PWD/install"
make && make install
```

### CI 测试

线上 CI 不运行 LC-3 仿真，执行两项轻量验证：

```bash
CI=true python3 tests/run_tests.py
python3 tests/oracle.py
```

其中 `CI=true python3 tests/run_tests.py` 只做 golden 对比，确认构建环境生成的汇编与本地提交的 golden 文件完全一致；`python3 tests/oracle.py` 用 GCC 生成本机 ELF，验证所有注册用例的期望输出或全局变量值。线上仍不启动 `lc3sim`，因为 LC-3 与 GCC 的真实执行对拍已经由本地完整测试负责。

当前测试规模：

- 49 个端到端 C 用例
- 覆盖默认模式、手写者风格、输入输出、数组、指针、复合赋值、乘除模、短路逻辑和调试注释
- 本地用 GCC ELF 直接对拍全部注册用例的 LC-3 仿真实际结果
- 本地额外验证 4 种参数组合：默认、`-d`、`--beginner-style`、`-d --beginner-style`

### 更新 golden

当代码生成输出发生预期变化时，需要重新生成 golden 文件：

```bash
python3 -m compiler_lc3 tests/cases/example.c -o tests/golden/example.asm
python3 -m compiler_lc3 tests/cases/beginner_example.c -o tests/golden/beginner_example.asm --beginner-style
```

## Release

GitHub Actions release workflow 在推送 `v*` tag 时触发：

```bash
git tag v0.1.0
git push origin v0.1.0
```

流程为：

1. Linux 上运行 `CI=true python3 tests/run_tests.py` 做 golden 对比，并运行 `python3 tests/oracle.py` 做 GCC oracle。
2. Linux / Windows / macOS 构建 portable 包。
3. tag 构建成功后上传到 GitHub Releases。

## 开发说明

- 新语法通常需要同步修改 `lexer.py`、`parser.py`、`ast.py`、`optimizer.py` 和 `codegen.py`。
- 新功能应添加 `tests/cases/*.c`，注册到 `tests/run_tests.py`，并生成对应 `tests/golden/*.asm`。
- 影响注释输出的改动需要确认 `verify_debug_comments()` 通过。
- 影响输出模式的改动应至少验证默认、`-d`、`--beginner-style`、`-d --beginner-style`。
