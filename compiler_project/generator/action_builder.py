#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ActionBuilder（while / if / relop 最终修复版）
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
    if isinstance(x, Node):
        return x.value
    return str(x)


# ===================== 基本结构 =====================

def program(children):
    node = Node("program", children)
    TACGEN.save(TAC_OUTPUT_FILE)
    return node


def var_decl(children):
    return Node("var_decl", children)


def assign(children):
    left = children[0].value
    right = children[2]
    TACGEN.emit("ASSIGN", v(right), None, left)
    return Node("assign", children)


# ===================== 表达式 =====================

def expr(children):
    return children[1](children[0])


def expr_tail_empty(children):
    return lambda x: x


def expr_tail_add(children):
    term, tail = children[1], children[2]
    def f(left):
        t = TACGEN.new_temp()
        TACGEN.emit("ADD", v(left), v(term), t)
        return tail(t)
    return f


def expr_tail_sub(children):
    term, tail = children[1], children[2]
    def f(left):
        t = TACGEN.new_temp()
        TACGEN.emit("SUB", v(left), v(term), t)
        return tail(t)
    return f


def term(children):
    return children[1](children[0])


def term_tail_empty(children):
    return lambda x: x


def term_tail_mul(children):
    factor, tail = children[1], children[2]
    def f(left):
        t = TACGEN.new_temp()
        TACGEN.emit("MUL", v(left), v(factor), t)
        return tail(t)
    return f


def term_tail_div(children):
    factor, tail = children[1], children[2]
    def f(left):
        t = TACGEN.new_temp()
        TACGEN.emit("DIV", v(left), v(factor), t)
        return tail(t)
    return f


def factor_id(children):
    return children[0].value


def factor_num(children):
    return children[0].value


def factor_expr(children):
    return children[1]


# ===================== 关系运算符（关键修复点） =====================

def relop(children):
    # children[0] 是 Token，如 Token(LT, '<')
    return children[0].type


# ===================== 条件 =====================

def condition_rel(children):
    left, op, right = children
    t = TACGEN.new_temp()
    TACGEN.emit(op, v(left), v(right), t)
    return t


def condition_odd(children):
    exprv = children[1]
    t = TACGEN.new_temp()
    TACGEN.emit("ODD", v(exprv), None, t)
    return t


# ===================== if / while =====================

def if_stmt(children):
    cond = children[1]
    Lend = TACGEN.new_label()
    TACGEN.emit("IF_FALSE", v(cond), None, Lend)
    return Node("if_stmt", children)


def while_stmt(children):
    cond = children[1]
    Lbegin = TACGEN.new_label()
    Lend = TACGEN.new_label()

    TACGEN.emit("LABEL", None, None, Lbegin)
    TACGEN.emit("IF_FALSE", v(cond), None, Lend)
    # 循环体 stmt 的 TAC 已在归约时生成
    TACGEN.emit("GOTO", None, None, Lbegin)
    TACGEN.emit("LABEL", None, None, Lend)

    return Node("while_stmt", children)


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

    "<relop> -> EQ": relop,
    "<relop> -> NE": relop,
    "<relop> -> LT": relop,
    "<relop> -> GT": relop,
    "<relop> -> LE": relop,
    "<relop> -> GE": relop,

    "<condition> -> <expr> <relop> <expr>": condition_rel,
    "<condition> -> ODD <expr>": condition_odd,

    "<if_stmt> -> IF <condition> THEN <stmt>": if_stmt,
    "<while_stmt> -> WHILE <condition> DO <stmt>": while_stmt,
}


# ===================== ActionBuilder =====================

class ActionBuilder:
    def __init__(self, parser_file: str):
        self.parser_file = parser_file

    def build(self) -> str:
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
        for k, f in ACTIONS.items():
            injected.append(f"    {k!r}: {f.__name__},\n")
        injected.append("}\n\n")

        injected.append("EXPORT_TAC = TACGEN\n")

        return "".join(injected)
