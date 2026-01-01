#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque

from generator.action_builder import TAC_OUTPUT_FILE

ACTIONS = {}

def parse(tokens, verbose=False):
    token_types = [t.type for t in tokens] + ['$']
    value_stack = []

    stack = deque(['$', '<program>'])
    i = 0

    while stack:
        top = stack.pop()
        lookahead = token_types[i]

        if top == lookahead == '$':
            return value_stack[-1] if value_stack else None

        if isinstance(top, tuple) and top[0] == '@REDUCE@':
            _, lhs, rhs = top
            if rhs != ['ε']:
                children = value_stack[-len(rhs):]
                del value_stack[-len(rhs):]
            else:
                children = []

            key = f"{lhs} -> {' '.join(rhs)}"
            node = ACTIONS[key](children) if key in ACTIONS else None
            value_stack.append(node)
            continue

        if not top.startswith('<'):
            if top == lookahead:
                value_stack.append(tokens[i])
                i += 1
                continue

            tok = tokens[i]
            line = getattr(tok, 'line', '?')
            raise SyntaxError(
                f"语法错误（第 {line} 行）：期望 {top}，得到 {tok.type} ({tok.value})"
            )

        key = (top, lookahead)
        if key not in PARSE_TABLE:
            tok = tokens[i]
            line = getattr(tok, 'line', '?')
            expected = sorted({t for (A, t) in PARSE_TABLE if A == top})
            raise SyntaxError(
                f"语法错误（第 {line} 行）：遇到 {tok.type} ({tok.value})，期望 {expected}"
            )

        prod = PARSE_TABLE[key]
        stack.append(('@REDUCE@', top, prod))
        for sym in reversed(prod):
            if sym != 'ε':
                stack.append(sym)

    return None

PARSE_TABLE = {
    ('<assign_stmt>', 'IDENTIFIER'): ['IDENTIFIER', 'ASSIGN', '<expr>'],
    ('<call_stmt>', 'CALL'): ['CALL', 'IDENTIFIER'],
    ('<compound_stmt>', 'BEGIN'): ['BEGIN', '<stmt_list>', 'END'],
    ('<condition>', 'IDENTIFIER'): ['<expr>', '<relop>', '<expr>'],
    ('<condition>', 'LPAREN'): ['<expr>', '<relop>', '<expr>'],
    ('<condition>', 'NUMBER'): ['<expr>', '<relop>', '<expr>'],
    ('<condition>', 'ODD'): ['ODD', '<expr>'],
    ('<const_decl_part>', 'CONST'): ['CONST', '<const_list>', 'SEMI'],
    ('<const_list>', 'IDENTIFIER'): ['IDENTIFIER', 'EQ', 'NUMBER', '<const_list_tail>'],
    ('<const_list_tail>', 'COMMA'): ['COMMA', 'IDENTIFIER', 'EQ', 'NUMBER', '<const_list_tail>'],
    ('<const_list_tail>', 'SEMI'): ['ε'],
    ('<decl_part>', 'BEGIN'): ['ε'],
    ('<decl_part>', 'CONST'): ['<const_decl_part>', '<var_decl_part>', '<proc_decl_part>'],
    ('<decl_part>', 'PROCEDURE'): ['<proc_decl_part>'],
    ('<decl_part>', 'VAR'): ['<var_decl_part>', '<proc_decl_part>'],
    ('<expr>', 'IDENTIFIER'): ['<term>', '<expr_tail>'],
    ('<expr>', 'LPAREN'): ['<term>', '<expr_tail>'],
    ('<expr>', 'NUMBER'): ['<term>', '<expr_tail>'],
    ('<expr_tail>', 'DO'): ['ε'],
    ('<expr_tail>', 'END'): ['ε'],
    ('<expr_tail>', 'EQ'): ['ε'],
    ('<expr_tail>', 'GE'): ['ε'],
    ('<expr_tail>', 'GT'): ['ε'],
    ('<expr_tail>', 'LE'): ['ε'],
    ('<expr_tail>', 'LT'): ['ε'],
    ('<expr_tail>', 'MINUS'): ['MINUS', '<term>', '<expr_tail>'],
    ('<expr_tail>', 'NE'): ['ε'],
    ('<expr_tail>', 'PLUS'): ['PLUS', '<term>', '<expr_tail>'],
    ('<expr_tail>', 'RPAREN'): ['ε'],
    ('<expr_tail>', 'SEMI'): ['ε'],
    ('<expr_tail>', 'THEN'): ['ε'],
    ('<factor>', 'IDENTIFIER'): ['IDENTIFIER'],
    ('<factor>', 'LPAREN'): ['LPAREN', '<expr>', 'RPAREN'],
    ('<factor>', 'NUMBER'): ['NUMBER'],
    ('<ident_list>', 'IDENTIFIER'): ['IDENTIFIER', '<ident_list_rest>'],
    ('<ident_list_rest>', 'COMMA'): ['COMMA', 'IDENTIFIER', '<ident_list_rest>'],
    ('<ident_list_rest>', 'SEMI'): ['ε'],
    ('<if_stmt>', 'IF'): ['IF', '<condition>', 'THEN', '<stmt>'],
    ('<proc_decl>', 'PROCEDURE'): ['PROCEDURE', 'IDENTIFIER', 'SEMI', '<program>', 'SEMI'],
    ('<proc_decl_part>', 'BEGIN'): ['ε'],
    ('<proc_decl_part>', 'PROCEDURE'): ['<proc_decl>', '<proc_decl_part>'],
    ('<program>', 'BEGIN'): ['<decl_part>', '<compound_stmt>', 'DOT'],
    ('<program>', 'CONST'): ['<decl_part>', '<compound_stmt>', 'DOT'],
    ('<program>', 'PROCEDURE'): ['<decl_part>', '<compound_stmt>', 'DOT'],
    ('<program>', 'VAR'): ['<decl_part>', '<compound_stmt>', 'DOT'],
    ('<relop>', 'EQ'): ['EQ'],
    ('<relop>', 'GE'): ['GE'],
    ('<relop>', 'GT'): ['GT'],
    ('<relop>', 'LE'): ['LE'],
    ('<relop>', 'LT'): ['LT'],
    ('<relop>', 'NE'): ['NE'],
    ('<stmt>', 'BEGIN'): ['<compound_stmt>'],
    ('<stmt>', 'CALL'): ['<call_stmt>'],
    ('<stmt>', 'END'): ['ε'],
    ('<stmt>', 'IDENTIFIER'): ['<assign_stmt>'],
    ('<stmt>', 'IF'): ['<if_stmt>'],
    ('<stmt>', 'SEMI'): ['ε'],
    ('<stmt>', 'WHILE'): ['<while_stmt>'],
    ('<stmt_list>', 'BEGIN'): ['<stmt>', '<stmt_list_tail>'],
    ('<stmt_list>', 'CALL'): ['<stmt>', '<stmt_list_tail>'],
    ('<stmt_list>', 'END'): ['<stmt>', '<stmt_list_tail>'],
    ('<stmt_list>', 'IDENTIFIER'): ['<stmt>', '<stmt_list_tail>'],
    ('<stmt_list>', 'IF'): ['<stmt>', '<stmt_list_tail>'],
    ('<stmt_list>', 'SEMI'): ['<stmt>', '<stmt_list_tail>'],
    ('<stmt_list>', 'WHILE'): ['<stmt>', '<stmt_list_tail>'],
    ('<stmt_list_tail>', 'END'): ['ε'],
    ('<stmt_list_tail>', 'SEMI'): ['SEMI', '<stmt>', '<stmt_list_tail>'],
    ('<term>', 'IDENTIFIER'): ['<factor>', '<term_tail>'],
    ('<term>', 'LPAREN'): ['<factor>', '<term_tail>'],
    ('<term>', 'NUMBER'): ['<factor>', '<term_tail>'],
    ('<term_tail>', 'DIV'): ['DIV', '<factor>', '<term_tail>'],
    ('<term_tail>', 'DO'): ['ε'],
    ('<term_tail>', 'END'): ['ε'],
    ('<term_tail>', 'EQ'): ['ε'],
    ('<term_tail>', 'GE'): ['ε'],
    ('<term_tail>', 'GT'): ['ε'],
    ('<term_tail>', 'LE'): ['ε'],
    ('<term_tail>', 'LT'): ['ε'],
    ('<term_tail>', 'MINUS'): ['ε'],
    ('<term_tail>', 'MULT'): ['MULT', '<factor>', '<term_tail>'],
    ('<term_tail>', 'NE'): ['ε'],
    ('<term_tail>', 'PLUS'): ['ε'],
    ('<term_tail>', 'RPAREN'): ['ε'],
    ('<term_tail>', 'SEMI'): ['ε'],
    ('<term_tail>', 'THEN'): ['ε'],
    ('<var_decl_part>', 'VAR'): ['VAR', '<ident_list>', 'SEMI'],
    ('<while_stmt>', 'WHILE'): ['WHILE', '<condition>', 'DO', '<stmt>'],
}

# ====== Semantic Actions & TAC ======
from src.runtime.ctx import TACContext
from src.runtime.token import Node

TACGEN = TACContext()

def v(x):
    if isinstance(x, Node):
        return x.value
    return str(x)


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


def expr(children):
    return children[1](children[0])


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


def expr_tail_empty(children):
    return lambda x: x


def term(children):
    return children[1](children[0])


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


def term_tail_empty(children):
    return lambda x: x


def factor_id(children):
    return children[0].value


def factor_num(children):
    return children[0].value


def factor_expr(children):
    return children[1]


def relop(children):
    # children[0] 是 Token，如 Token(LT, '<')
    return children[0].type


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


ACTIONS = {
    '<program> -> <decl_part> <compound_stmt> DOT': program,
    '<var_decl_part> -> VAR <ident_list> SEMI': var_decl,
    '<assign_stmt> -> IDENTIFIER ASSIGN <expr>': assign,
    '<expr> -> <term> <expr_tail>': expr,
    '<expr_tail> -> PLUS <term> <expr_tail>': expr_tail_add,
    '<expr_tail> -> MINUS <term> <expr_tail>': expr_tail_sub,
    '<expr_tail> -> ε': expr_tail_empty,
    '<term> -> <factor> <term_tail>': term,
    '<term_tail> -> MULT <factor> <term_tail>': term_tail_mul,
    '<term_tail> -> DIV <factor> <term_tail>': term_tail_div,
    '<term_tail> -> ε': term_tail_empty,
    '<factor> -> IDENTIFIER': factor_id,
    '<factor> -> NUMBER': factor_num,
    '<factor> -> LPAREN <expr> RPAREN': factor_expr,
    '<relop> -> EQ': relop,
    '<relop> -> NE': relop,
    '<relop> -> LT': relop,
    '<relop> -> GT': relop,
    '<relop> -> LE': relop,
    '<relop> -> GE': relop,
    '<condition> -> <expr> <relop> <expr>': condition_rel,
    '<condition> -> ODD <expr>': condition_odd,
    '<if_stmt> -> IF <condition> THEN <stmt>': if_stmt,
    '<while_stmt> -> WHILE <condition> DO <stmt>': while_stmt,
}

EXPORT_TAC = TACGEN
