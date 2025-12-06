# Auto-generated lexer
import re

class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value
    def __repr__(self):
        return f'Token({self.type}, {self.value})'

TOKEN_REGEX = [
    ('IF', re.compile(r'if')),
    ('ELSE', re.compile(r'else')),
    ('WHILE', re.compile(r'while')),
    ('RETURN', re.compile(r'return')),
    ('INT', re.compile(r'int')),
    ('VOID', re.compile(r'void')),
    ('SET', re.compile(r'set')),
    ('IDENTIFIER', re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')),
    ('NUMBER', re.compile(r'[0-9]+')),
    ('STRING', re.compile(r'"([^"\\]|\\.)*"')),
    ('COMMENT', re.compile(r'//.*')),
    ('COMMENT', re.compile(r'/\*[\s\S]*?\*/')),
    ('LE', re.compile(r'<=')),
    ('GE', re.compile(r'>=')),
    ('EQ', re.compile(r'==')),
    ('NE', re.compile(r'!=')),
    ('LT', re.compile(r'<')),
    ('GT', re.compile(r'>')),
    ('ASSIGN', re.compile(r'=')),
    ('PLUS', re.compile(r'\+')),
    ('MINUS', re.compile(r'\-')),
    ('MULT', re.compile(r'\*')),
    ('DIV', re.compile(r'/')),
    ('LPAREN', re.compile(r'\(')),
    ('RPAREN', re.compile(r'\)')),
    ('LBRACE', re.compile(r'\{')),
    ('RBRACE', re.compile(r'\}')),
    ('SEMI', re.compile(r';')),
    ('COMMA', re.compile(r',')),
    ('WS', re.compile(r'[ \t\r\n]+')),
]

def tokenize(code):
    tokens = []
    i = 0
    length = len(code)

    while i < length:
        match = None
        for token_name, regex in TOKEN_REGEX:
            m = regex.match(code, i)
            if m:
                match = m
                value = m.group()
                # 跳过空白和注释（支持 COMMENT_LINE、COMMENT_BLOCK）
                if token_name not in ('WS', 'COMMENT', 'COMMENT_LINE', 'COMMENT_BLOCK'):
                    tokens.append(Token(token_name, value))
                i = m.end()
                break
        if not match:
            raise SyntaxError(f'Unknown token at index {i}: {code[i]}')
    return tokens
