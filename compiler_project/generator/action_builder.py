#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ActionBuilder（与当前 yacc_builder.py 100% 对齐版）

设计前提（非常重要）：
- yacc_builder.py 生成的 temp_parser.py 使用 **@REDUCE@ 标记**
- 归约点格式为：
    ('@REDUCE@', lhs, rhs)
- parser 在归约时执行：
    key = f"{lhs} -> {' '.join(rhs)}"
    ACTIONS[key](children)

本 ActionBuilder 只做一件事：
👉 向 temp_parser.py 注入：
   1. TACContext / Node
   2. 所有 action 函数
   3. ACTIONS 映射（key = 产生式字符串）
❌ 不再生成新的 parse
❌ 不再二次驱动语法分析
"""

import os
import inspect

from src.runtime.ctx import TACContext
from src.runtime.token import Node


# ===================== 三地址码输出位置 =====================
TAC_OUTPUT_FILE = os.path.join("generated_compiler", "tac_output.txt")


# ===================== Action Functions =====================

TACGEN = TACContext()


def program(children):
    node = Node("program", children)
    TACGEN.save(TAC_OUTPUT_FILE)
    return node


def var_decl(children):
    node = Node("var_decl", children)
    for c in children:
        TACGEN.emit("VAR", str(c))
    return node


def assign(children):
    node = Node("assign", children)
    left = str(children[0])
    right = str(children[-1])
    TACGEN.emit("ASSIGN", right, None, left)
    return node


def add(children):
    node = Node("add", children)
    t = TACGEN.new_temp()
    TACGEN.emit("ADD", str(children[0]), str(children[2]), t)
    return t


def sub(children):
    node = Node("sub", children)
    t = TACGEN.new_temp()
    TACGEN.emit("SUB", str(children[0]), str(children[2]), t)
    return t


def mul(children):
    node = Node("mul", children)
    t = TACGEN.new_temp()
    TACGEN.emit("MUL", str(children[0]), str(children[2]), t)
    return t


def div(children):
    node = Node("div", children)
    t = TACGEN.new_temp()
    TACGEN.emit("DIV", str(children[0]), str(children[2]), t)
    return t


def pass_through(children):
    """默认动作：直接返回唯一子节点"""
    return children[0] if children else None


# ===================== ACTION TABLE（产生式字符串 → 函数） =====================

ACTIONS = {
    "<program> -> <decl_part> <compound_stmt> DOT": program,

    "<var_decl_part> -> VAR <ident_list> SEMI": var_decl,

    "<assign_stmt> -> IDENTIFIER ASSIGN <expr>": assign,

    "<expr_tail> -> PLUS <term> <expr_tail>": add,
    "<expr_tail> -> MINUS <term> <expr_tail>": sub,

    "<term_tail> -> MULT <factor> <term_tail>": mul,
    "<term_tail> -> DIV <factor> <term_tail>": div,

    # 兜底规则（无语义，仅传递）
    "<expr> -> <term> <expr_tail>": pass_through,
    "<term> -> <factor> <term_tail>": pass_through,
    "<factor> -> IDENTIFIER": pass_through,
    "<factor> -> NUMBER": pass_through,
    "<factor> -> LPAREN <expr> RPAREN": pass_through,
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

        written = set()
        for func in ACTIONS.values():
            if func not in written:
                injected.append(inspect.getsource(func))
                injected.append("\n\n")
                written.add(func)

        injected.append("ACTIONS = {\n")
        for k, v in ACTIONS.items():
            injected.append(f"    {k!r}: {v.__name__},\n")
        injected.append("}\n\n")

        injected.append("# 对外导出 TAC\n")
        injected.append("EXPORT_TAC = TACGEN\n")

        return "".join(injected)
