# lex_builder.py
"""
LexBuilder：读取 lex_rules.lex，生成 lexer.py（高效稳定版）
"""

import re
import os

class LexBuilder:
    def __init__(self, lex_file):
        self.lex_file = lex_file
        self.rules = []  # (token_name, regex)

    def load_rules(self):
        """
        从 lex_rules.lex 文件读取规则
        格式：
            TOKEN_NAME   REGEX_PATTERN
        """
        if not os.path.exists(self.lex_file):
            raise FileNotFoundError(f"{self.lex_file} 不存在")

        with open(self.lex_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split(maxsplit=1)
                if len(parts) != 2:
                    continue

                token_name, pattern = parts
                self.rules.append((token_name, pattern))

    def build(self):
        """
        返回完整的 lexer.py 内容
        """
        self.load_rules()

        code = "# Auto-generated lexer\n"
        code += "import re\n\n"

        # Token 类
        code += "class Token:\n"
        code += "    def __init__(self, type_, value):\n"
        code += "        self.type = type_\n"
        code += "        self.value = value\n"
        code += "    def __repr__(self):\n"
        code += "        return f'Token({self.type}, {self.value})'\n\n"

        # 生成 TOKEN_REGEX 列表，并提前 compile
        code += "TOKEN_REGEX = [\n"
        for token_name, pattern in self.rules:
            code += f"    ('{token_name}', re.compile(r'{pattern}')),\n"
        code += "]\n\n"

        # 主 tokenize 函数
        code += "def tokenize(code):\n"
        code += "    tokens = []\n"
        code += "    i = 0\n"
        code += "    length = len(code)\n\n"
        code += "    while i < length:\n"
        code += "        match = None\n"
        code += "        for token_name, regex in TOKEN_REGEX:\n"
        code += "            m = regex.match(code, i)\n"
        code += "            if m:\n"
        code += "                match = m\n"
        code += "                value = m.group()\n"
        code += "                # 跳过空白和注释（支持 COMMENT_LINE、COMMENT_BLOCK）\n"
        code += "                if token_name not in ('WS', 'COMMENT', 'COMMENT_LINE', 'COMMENT_BLOCK'):\n"
        code += "                    tokens.append(Token(token_name, value))\n"
        code += "                i = m.end()\n"
        code += "                break\n"
        code += "        if not match:\n"
        code += "            raise SyntaxError(f'Unknown token at index {i}: {code[i]}')\n"
        code += "    return tokens\n"

        return code
