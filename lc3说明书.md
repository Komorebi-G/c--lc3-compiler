# LC-3 与编译器子集说明

## 目标

本项目实现一个“可运行优先”的 C 子集到 LC-3 汇编编译器。

目标不是兼容完整 C，而是把一组明确受限的语法稳定地翻译为 LC-3 程序，并且让生成代码能在常见 LC-3 汇编器/模拟器环境中工作。

## LC-3 约束

LC-3 是教学 ISA，核心约束直接影响编译器设计：

- 8 个通用寄存器：`R0` 到 `R7`
- 常用约定：
  - `R6` 作为栈指针 `SP`
  - `R5` 作为帧指针 `FP`
  - `R7` 保存返回地址
- 只有很少的基础运算：
  - `ADD`
  - `AND`
  - `NOT`
- 控制流主要依靠条件码与 `BR`
- 过程调用使用 `JSR/RET`
- 内存访问使用 `LD/ST/LDR/STR/LEA`

参考：

- LC-3 TRAP 例程：<https://cs131.info/Assembly/Instructions/TRAPRoutines.html>
- LC-3 内存访问：<https://cs131.info/Assembly/Instructions/MemoryAccess.html>
- LC-3 栈帧与运行时栈：<https://www.cs.colostate.edu/~fsieker/misc/runtimeStack/runtimeStack.html>

## I/O 模型

LC-3 自带的 TRAP 例程中，本项目目前使用：

- `GETC` / `TRAP x20`
  - 读入一个字符
  - 返回值放在 `R0`
- `OUT` / `TRAP x21`
  - 输出 `R0` 中的单个字符
- `PUTS` / `TRAP x22`
  - 将 `R0` 视为字符串地址并输出，直到遇到 `0`
- `HALT` / `TRAP x25`
  - 程序结束

因此编译器当前内建支持以下运行时函数：

```c
int getchar(void);
int putchar(int ch);
int puts(char *s);
```

说明：

- `getchar()` 返回 ASCII 码整数
- `putchar(x)` 输出 `x` 的字符值，返回 `0`
- `puts(s)` 输出以 `0` 结尾的字符串，返回 `0`
- 当前 `puts` 最稳妥的用法是传字符串字面量

## 当前支持的 C 子集

### 1. 数据类型

只支持：

```c
int
```

约定：

- `int` 按 LC-3 的 16 位有符号整数处理
- 当前不做完整类型系统
- 没有 `char`、`short`、`long`、`struct`、`enum`

### 2. 顶层结构

支持：

- 全局变量定义
- 函数定义

示例：

```c
int g;
int limit = 10;

int add1(int x) {
    return x + 1;
}

int main() {
    return add1(limit);
}
```

### 3. 局部变量

支持：

```c
int a;
int b = 3;
```

当前实现约束：

- 不支持同名遮蔽，内层块不能重新声明与外层同名的局部变量或参数
- 所有局部变量在函数栈帧中预分配
- 为了保证运行结果稳定，未显式初始化的局部变量会在函数入口被清零

### 4. 语句

支持：

```c
if (...) { ... }
else if (...) { ... }
else { ... }

while (...) { ... }

for (init; cond; step) { ... }

break;
continue;
return expr;
return;
```

### 5. 表达式

支持：

- 整数字面量
- 字符串字面量
- 变量引用
- 函数调用
- 赋值表达式
- 括号
- 一元运算：
  - `-`
  - `!`
- 二元运算：
  - `+`
  - `-`
  - `<`
  - `<=`
  - `>`
  - `>=`
  - `==`
  - `!=`

逻辑约定：

- 条件判断遵循“`0` 为假，非 `0` 为真”
- 当前还未支持 `&&` 与 `||`

## 当前不支持的内容

以下内容暂未进入第一版：

- 指针运算
- 数组
- 结构体
- `switch`
- `do while`
- `++` / `--`
- `*` / `/` / `%`
- `&&` / `||`
- 预处理器
- 头文件
- 完整标准库
- `printf` / `scanf`

## 当前语法

```ebnf
program     ::= { global_decl | func_def }

global_decl ::= "int" ident [ "=" number ] ";"

func_def    ::= "int" ident "(" [ param_list ] ")" block
param_list  ::= "int" ident { "," "int" ident }

block       ::= "{" { decl | stmt } "}"
decl        ::= "int" ident [ "=" expr ] ";"

stmt        ::= expr ";"
              | if_stmt
              | while_stmt
              | for_stmt
              | "break" ";"
              | "continue" ";"
              | "return" [ expr ] ";"
              | block

if_stmt     ::= "if" "(" expr ")" stmt [ "else" stmt ]
while_stmt  ::= "while" "(" expr ")" stmt
for_stmt    ::= "for" "(" [ expr ] ";" [ expr ] ";" [ expr ] ")" stmt

expr        ::= assignment
assignment  ::= equality [ "=" assignment ]
equality    ::= relational { ("==" | "!=") relational }
relational  ::= additive { ("<" | "<=" | ">" | ">=") additive }
additive    ::= unary { ("+" | "-") unary }
unary       ::= primary | "-" unary | "!" unary
primary     ::= number
              | string
              | ident
              | ident "(" [ arg_list ] ")"
              | "(" expr ")"
arg_list    ::= expr { "," expr }
```

## 运行时与调用约定

### 栈帧模型

调用者：

- 从右到左压参数
- `JSR callee`
- 返回后由调用者弹出参数

被调用者：

1. 保存 `R7`
2. 保存旧 `R5`
3. 设置新的 `R5`
4. 预留局部变量空间
5. 执行函数体
6. 返回值放入 `R0`
7. 恢复 `R5`、`R7`
8. `RET`

### 帧内布局

当前约定：

- `FP + 0`：旧 `R5`
- `FP + 1`：保存的返回地址 `R7`
- `FP + 2`：第 1 个参数
- `FP + 3`：第 2 个参数
- ...
- `FP - 1`：第 1 个局部变量
- `FP - 2`：第 2 个局部变量

### 返回值

- 函数返回值统一放在 `R0`

## 编译策略

当前版本采用：

- 词法分析
- 递归下降语法分析
- 直接从 AST 生成 LC-3 汇编

控制流翻译方式：

- `if/else if/else` -> 条件判断 + 标签 + `BR`
- `while` -> 测试标签 + 循环体标签 + 退出标签
- `for` -> 初始化 + 测试标签 + 步进标签 + 退出标签
- `break` / `continue` -> 跳转到当前循环上下文记录的标签

表达式翻译方式：

- 结果默认放入 `R0`
- 复杂二元表达式通过运行时栈临时保存中间结果
- 比较运算最终归一化为 `0` 或 `1`

## 示例

### 回显直到回车

```c
int main() {
    int ch;
    while (1) {
        ch = getchar();
        if (ch == 10) {
            break;
        } else if (ch == 13) {
            continue;
        }
        putchar(ch);
    }
    putchar(10);
    return 0;
}
```

### 多函数与循环

```c
int sum_to(int n) {
    int i = 0;
    int acc = 0;
    for (i = 0; i < n; i = i + 1) {
        acc = acc + i;
    }
    return acc;
}

int main() {
    return sum_to(5);
}
```

## 后续计划

按优先级建议：

1. 加入 `&&`、`||` 和短路求值
2. 加入 `*`、`/`、`%` 与辅助运行时函数
3. 加入数组与地址传递
4. 加入更严格的语义检查
5. 加入测试集和自动化验证
