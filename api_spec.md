# Compiler Project API Specification

## 1. Token 接口

**文件**: `src/runtime/token.py`

### Token 数据结构

```
class Token:
    type: TokenType    # Token 类型，枚举 TokenType
    value: str         # 原始文本，例如 "abc", "123"
    line: int          # 行号，从 1 开始
    column: int        # 列号，从 1 开始
```

### TokenStream 接口

```
class TokenStream:
    def __init__(tokens: List[Token])
    peek() -> Token         # 查看当前 token，不消费
    next() -> Token         # 获取当前 token，并向后移动
    expect(type_name: TokenType) -> Token  # 匹配 token 类型，不匹配抛出 SyntaxError
```

**使用说明**：

- Lexer 输出 `List[Token]`，Parser 直接使用 `TokenStream` 遍历。
- EOF 用 `TokenType.EOF` 表示。

------

## 2. 中间代码生成上下文（Context）

**文件**: `src/runtime/ctx.py`

### Context 类接口

```
class Context:
    temp_counter: int      # 临时变量计数
    code: List[str]        # 已生成的三地址码
    
    def new_temp(type_: str) -> str:
        # 返回一个新的临时变量名称
        ...

    def emit(instr: str):
        # 向 code 列表追加一条三地址码指令
        ...

    def get_code() -> str:
        # 返回完整三地址码文本
        ...
```

**说明**：

- `type_` 可以是 `"int"`、`"bool"` 等，用于记录临时变量类型。
- `emit` 会自动将指令追加到 `code` 中。
- 最终 TAC 输出写入 `generated_compiler/tac_output.txt`。

------

## 3. Lexer 接口

**生成文件**: `generated_compiler/lexer.py`

```
class Lexer:
    def __init__(source_code: str)
    tokenize() -> List[Token]     # 将 source_code 转为 token 列表
```

**使用说明**：

- Lexer 根据 `lex_rules.lex` 自动生成。
- 输出 `List[Token]`，直接传给 Parser。

------

## 4. Parser 接口

**生成文件**: `generated_compiler/parser.py`

```
class Parser:
    def __init__(token_stream: TokenStream, ctx: Context)
    parse() -> None         # 执行语法分析，同时生成 TAC
```

**使用说明**：

- Parser 根据 `yacc_rules.bnf` + 语义动作生成。
- 解析过程中调用 `ctx.emit(...)` 写 TAC。
- TAC 最终写入 `tac_output.txt`。

------

## 5. TAC 输出规范

- 每条指令占一行。
- 典型格式：

```
t1 = 5
t2 = t1 + 3
a = t2
if t1 < t2 goto L1
goto L2
L1:
...
```

- 临时变量命名规则：`t{数字}`，如 `t1`、`t2`。
- 标签命名规则：`L{数字}`，如 `L1`、`L2`。

------

## 6. 文件调用流程（示例）

```
from generated_compiler.lexer import Lexer
from generated_compiler.parser import Parser
from src.runtime.token import TokenStream
from src.runtime.ctx import Context

source_code = "int a; a = 1 + 2;"
lexer = Lexer(source_code)
tokens = lexer.tokenize()
ts = TokenStream(tokens)
ctx = Context()
parser = Parser(ts, ctx)
parser.parse()

# 输出 TAC
with open("generated_compiler/tac_output.txt", "w") as f:
    f.write(ctx.get_code())
```