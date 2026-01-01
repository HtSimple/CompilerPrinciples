#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ActionBuilder（最终干净 TAC 版）

特性：
- ✅ 变量声明不生成任何 TAC
- ✅ 表达式 / 赋值生成标准三地址码
- ✅ 无 eval / 无 Token 泄漏
"""

import os
import inspect

from src.runtime.ctx import TACContext
from src.runtime.token import Node


# ===================== TAC 输出位置 =====================
TAC_OUTPUT_FILE = os.path.join("generated_compiler", "tac_output.txt")


# ===================== 全局 TAC 上下文 =====================
TACGEN = TACContext()


# ===================== 工具函数 =====================
def v(x):
    """统一取值：Node / Token / str"""
    if isinstance(x, Node):
        return x.value
    return str(x)


# ===================== Action Functions =====================

def program(children):
    node = Node("program", children)
    TACGEN.save(TAC_OUTPUT_FILE)
    return node


# ❌ 变量声明：只构 AST / 符号表，不生成 TAC
def var_decl(children):
    return Node("var_decl", children)


def assign(children):
    left = children[0].value
    right = children[2]
    TACGEN.emit("ASSIGN", v(right), None, left)
    return Node("assign", children)


# ---------- 表达式 ----------

def expr(children):
    left = children[0]
    tail = children[1]
    return tail(left)


def expr_tail_empty(children):
    return lambda x: x


def expr_tail_add(children):
    term = children[1]
    tail = children[2]

    def apply(left):
        t = TACGEN.new_temp()
        TACGEN.emit("ADD", v(left), v(term), t)
        return tail(t)

    return apply


def expr_tail_sub(children):
    term = children[1]
    tail = children[2]

    def apply(left):
        t = TACGEN.new_temp()
        TACGEN.emit("SUB", v(left), v(term), t)
        return tail(t)

    return apply


# ---------- 项 ----------

def term(children):
    left = children[0]
    tail = children[1]
    return tail(left)


def term_tail_empty(children):
    return lambda x: x


def term_tail_mul(children):
    factor = children[1]
    tail = children[2]

    def apply(left):
        t = TACGEN.new_temp()
        TACGEN.emit("MUL", v(left), v(factor), t)
        return tail(t)

    return apply


def term_tail_div(children):
    factor = children[1]
    tail = children[2]

    def apply(left):
        t = TACGEN.new_temp()
        TACGEN.emit("DIV", v(left), v(factor), t)
        return tail(t)

    return apply


# ---------- 因子 ----------

def factor_id(children):
    return children[0].value


def factor_num(children):
    return children[0].value


def factor_expr(children):
    return children[1]


# ===================== ACTION TABLE =====================

ACTIONS = {
    "<program> -> <decl_part> <compound_stmt> DOT": program,

    "<var_decl_part> -> VAR <ident_list> SEMI": var_decl,
    "<assign_stmt> -> IDENTIFIER ASSIGN <expr>": assign,

    "<expr> -> <term> <expr_tail>": expr,
    "<expr_tail> -> PLUS <term> <expr_tail>": expr_tail_add,
    "<expr_tail> -> MINUS <term> <expr_tail>": expr_tail_sub,
    "<expr_tail> -> ε": expr_tail_empty,

    "<term> -> <factor> <term_tail>": term,
    "<term_tail> -> MULT <factor> <term_tail>": term_tail_mul,
    "<term_tail> -> DIV <factor> <term_tail>": term_tail_div,
    "<term_tail> -> ε": term_tail_empty,

    "<factor> -> IDENTIFIER": factor_id,
    "<factor> -> NUMBER": factor_num,
    "<factor> -> LPAREN <expr> RPAREN": factor_expr,
}


# ===================== ActionBuilder =====================

class ActionBuilder:
    def __init__(self, parser_file: str):
        self.parser_file = parser_file

    def build(self) -> str:
        if not os.path.exists(self.parser_file):
            raise FileNotFoundError(self.parser_file)

        with open(self.parser_file, "r", encoding="utf-8") as f:
            parser_code = f.read()

        injected = []
        injected.append(parser_code)
        injected.append("\n\n# ====== Semantic Actions & TAC ======\n")
        injected.append("from src.runtime.ctx import TACContext\n")
        injected.append("from src.runtime.token import Node\n\n")
        injected.append("TACGEN = TACContext()\n\n")

        injected.append(inspect.getsource(v))
        injected.append("\n\n")

        written = set()
        for func in ACTIONS.values():
            if func not in written:
                injected.append(inspect.getsource(func))
                injected.append("\n\n")
                written.add(func)

        injected.append("ACTIONS = {\n")
        for k, func in ACTIONS.items():
            injected.append(f"    {k!r}: {func.__name__},\n")
        injected.append("}\n\n")

        injected.append("EXPORT_TAC = TACGEN\n")

        return "".join(injected)
