# src/runtime/token.py
# --------------------------------------------
# Token 数据结构，供 Lexer/Both Parser/CodeGen 使用
# --------------------------------------------

from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    # 基本类型
    IDENTIFIER = auto()      # 标识符
    NUMBER = auto()          # 数字字面量
    STRING = auto()          # 字符串字面量

    # 关键字
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    RETURN = auto()
    INT = auto()
    VOID = auto()

    # 运算符
    PLUS = auto()            # +
    MINUS = auto()           # -
    MULT = auto()            # *
    DIV = auto()             # /
    ASSIGN = auto()          # =
    EQ = auto()              # ==
    NE = auto()              # !=
    LT = auto()              # <
    GT = auto()              # >
    LE = auto()              # <=
    GE = auto()              # >=

    # 界符
    LPAREN = auto()          # (
    RPAREN = auto()          # )
    LBRACE = auto()          # {
    RBRACE = auto()          # }
    SEMI = auto()            # ;
    COMMA = auto()           # ,

    # 文件结束
    EOF = auto()


@dataclass
class Token:
    type: TokenType      # Token 类型
    value: str           # 原始文本，例如 "abc"、"123"
    line: int            # 所在行号
    column: int          # 所在列号

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"


class TokenStream:
    """
    Token 序列包装器，供 Parser 使用
    提供 peek()/next()/expect() 等方法
    """
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        """返回当前 token，不移动位置"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, "", -1, -1)

    def next(self):
        """返回当前 token，并将位置移动到下一个"""
        tok = self.peek()
        self.pos += 1
        return tok

    def expect(self, type_name: TokenType):
        """匹配指定类型 token，否则抛出语法错误"""
        tok = self.peek()
        if tok.type != type_name:
            raise SyntaxError(
                f"Expected token {type_name.name}, got {tok.type.name} "
                f"at line {tok.line}, col {tok.column}"
            )
        self.pos += 1
        return tok
