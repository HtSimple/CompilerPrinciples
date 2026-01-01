#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
from generator.action_builder import TAC_OUTPUT_FILE

ACTIONS = {}  # 将由 ActionBuilder 注入

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
            raise SyntaxError(f'期望 {top}, 得到 {lookahead}')

        key = (top, lookahead)
        if key not in PARSE_TABLE:
            raise SyntaxError(f'分析表无条目: {key}')

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
    """统一取值：Node / Token / str"""
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
    left = children[0]
    tail = children[1]
    return tail(left)


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


def expr_tail_empty(children):
    return lambda x: x


def term(children):
    left = children[0]
    tail = children[1]
    return tail(left)


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


def term_tail_empty(children):
    return lambda x: x


def factor_id(children):
    return children[0].value


def factor_num(children):
    return children[0].value


def factor_expr(children):
    return children[1]


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
}

EXPORT_TAC = TACGEN
