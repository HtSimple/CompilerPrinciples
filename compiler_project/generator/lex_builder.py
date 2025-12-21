import os
import string

###############################################################################
# 基础数据结构
###############################################################################

class NFAState:
    _id = 0

    def __init__(self):
        self.id = NFAState._id
        NFAState._id += 1
        self.transitions = {}      # char -> set(states)
        self.epsilon = set()        # ε-transitions
        self.accepting = None       # token type


class NFA:
    def __init__(self, start, end):
        self.start = start
        self.end = end


###############################################################################
# 正则表达式 → NFA（Thompson 构造）
###############################################################################

class RegexParser:
    """
    支持：
    - 字符
    - []
    - *
    - |
    - ()
    """

    def __init__(self, regex):
        self.regex = regex
        self.pos = 0

    def parse(self):
        return self.expr()

    def expr(self):
        term = self.term()
        while self._peek() == '|':
            self._next()
            right = self.term()
            s = NFAState()
            e = NFAState()
            s.epsilon |= {term.start, right.start}
            term.end.epsilon.add(e)
            right.end.epsilon.add(e)
            term = NFA(s, e)
        return term

    def term(self):
        factors = []
        while self._peek() and self._peek() not in ')|':
            factors.append(self.factor())
        if not factors:
            s = NFAState()
            e = NFAState()
            s.epsilon.add(e)
            return NFA(s, e)
        nfa = factors[0]
        for f in factors[1:]:
            nfa.end.epsilon.add(f.start)
            nfa = NFA(nfa.start, f.end)
        return nfa

    def factor(self):
        base = self.base()
        if self._peek() == '*':
            self._next()
            s = NFAState()
            e = NFAState()
            s.epsilon |= {base.start, e}
            base.end.epsilon |= {base.start, e}
            return NFA(s, e)
        return base

    def base(self):
        ch = self._peek()
        if ch == '(':
            self._next()
            nfa = self.expr()
            self._next()  # )
            return nfa
        elif ch == '[':
            return self.char_class()
        else:
            return self.literal(self._next())

    def literal(self, ch):
        s = NFAState()
        e = NFAState()
        s.transitions.setdefault(ch, set()).add(e)
        return NFA(s, e)

    def char_class(self):
        self._next()  # [
        chars = set()
        while self._peek() != ']':
            c = self._next()
            if self._peek() == '-':
                self._next()
                end = self._next()
                for x in range(ord(c), ord(end) + 1):
                    chars.add(chr(x))
            else:
                chars.add(c)
        self._next()  # ]
        s = NFAState()
        e = NFAState()
        for c in chars:
            s.transitions.setdefault(c, set()).add(e)
        return NFA(s, e)

    def _peek(self):
        return self.regex[self.pos] if self.pos < len(self.regex) else None

    def _next(self):
        ch = self.regex[self.pos]
        self.pos += 1
        return ch


###############################################################################
# NFA → DFA
###############################################################################

def epsilon_closure(states):
    stack = list(states)
    closure = set(states)
    while stack:
        s = stack.pop()
        for nxt in s.epsilon:
            if nxt not in closure:
                closure.add(nxt)
                stack.append(nxt)
    return closure


def move(states, ch):
    result = set()
    for s in states:
        result |= s.transitions.get(ch, set())
    return result


###############################################################################
# DFA 最小化
###############################################################################

def minimize_dfa(dfa_states, accept_map):
    num_states = len(dfa_states)
    alphabet = set()
    for trans in dfa_states:
        alphabet |= set(trans.keys())

    # 1. 初始划分（按 token 类型 + 非接受）
    partitions = {}
    for s in range(num_states):
        key = accept_map.get(s, None)  # None = 非接受
        partitions.setdefault(key, set()).add(s)

    P = list(partitions.values())

    # 2. 反复细化
    changed = True
    while changed:
        changed = False
        new_P = []

        for group in P:
            splitter = {}
            for s in group:
                sig = []
                for ch in alphabet:
                    to = dfa_states[s].get(ch)
                    idx = None
                    for i, g in enumerate(P):
                        if to in g:
                            idx = i
                            break
                    sig.append(idx)
                splitter.setdefault(tuple(sig), set()).add(s)

            if len(splitter) > 1:
                changed = True
                new_P.extend(splitter.values())
            else:
                new_P.append(group)

        P = new_P

    # 3. 构造新 DFA
    state_map = {}
    for i, group in enumerate(P):
        for s in group:
            state_map[s] = i

    new_dfa = [{} for _ in P]
    new_accept = {}

    for old_s, new_s in state_map.items():
        for ch, to in dfa_states[old_s].items():
            new_dfa[new_s][ch] = state_map[to]

        if old_s in accept_map:
            new_accept[new_s] = accept_map[old_s]

    return new_dfa, new_accept

###############################################################################
# 生成 lexer.py
###############################################################################

def generate_lexer(dfa_states, accept_map):
    lines = []

    lines.append("class Token:")
    lines.append("    def __init__(self, type_, value):")
    lines.append("        self.type = type_")
    lines.append("        self.value = value")
    lines.append("    def __repr__(self):")
    lines.append("        return f\"Token({self.type}, {self.value})\"")
    lines.append("")

    lines.append("class Lexer:")
    lines.append("    def __init__(self, text):")
    lines.append("        self.text = text")
    lines.append("        self.pos = 0")
    lines.append("")
    lines.append("    def tokenize(self):")
    lines.append("        tokens = []")
    lines.append("        while self.pos < len(self.text):")
    lines.append("            if self.text[self.pos] in ' \\t\\r\\n':")
    lines.append("                self.pos += 1")
    lines.append("                continue")
    lines.append("")
    lines.append("            state = 0")
    lines.append("            last_accept = None")
    lines.append("            last_pos = self.pos")
    lines.append("            i = self.pos")
    lines.append("")
    lines.append("            while i < len(self.text) and self.text[i] in TRANS[state]:")
    lines.append("                state = TRANS[state][self.text[i]]")
    lines.append("                i += 1")
    lines.append("                if state in ACCEPT:")
    lines.append("                    last_accept = ACCEPT[state]")
    lines.append("                    last_pos = i")
    lines.append("")
    lines.append("            if last_accept is None:")
    lines.append("                raise SyntaxError(f\"Illegal character: {self.text[self.pos]!r}\")")
    lines.append("")
    lines.append("            value = self.text[self.pos:last_pos]")
    lines.append("            self.pos = last_pos")
    lines.append("")
    lines.append("            if last_accept != 'WS' and last_accept != 'COMMENT':")
    lines.append("                tok_type = last_accept")
    lines.append("                if tok_type == 'IDENTIFIER':")
    lines.append("                    if value == 'if': tok_type = 'IF'")
    lines.append("                    elif value == 'else': tok_type = 'ELSE'")
    lines.append("                    elif value == 'while': tok_type = 'WHILE'")
    lines.append("                    elif value == 'return': tok_type = 'RETURN'")
    lines.append("                    elif value == 'int': tok_type = 'INT'")
    lines.append("                    elif value == 'void': tok_type = 'VOID'")
    lines.append("                    elif value == 'set': tok_type = 'SET'")
    lines.append("                tokens.append(Token(tok_type, value))")
    lines.append("")
    lines.append("        return tokens")
    lines.append("")

    lines.append("TRANS = {")
    for i, trans in enumerate(dfa_states):
        lines.append(f"    {i}: {{")
        for ch, to in trans.items():
            lines.append(f"        {repr(ch)}: {to},")
        lines.append("    },")
    lines.append("}")
    lines.append("")
    lines.append("ACCEPT = {")
    for k, v in accept_map.items():
        lines.append(f"    {k}: {repr(v)},")
    lines.append("}")

    return "\n".join(lines)


###############################################################################
# LexBuilder
###############################################################################

class LexBuilder:
    def __init__(self, lex_rules_path: str):
        self.lex_rules_path = lex_rules_path

    def build(self) -> str:
        rules = []
        with open(self.lex_rules_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                name, regex = line.split(None, 1)
                rules.append((name, regex))

        start = NFAState()

        for name, regex in rules:
            parser = RegexParser(regex)
            nfa = parser.parse()
            nfa.end.accepting = name
            start.epsilon.add(nfa.start)

        charset = set(string.printable)
        dfa_states = []
        dfa_map = {}
        accept_map = {}

        start_closure = epsilon_closure({start})
        dfa_map[frozenset(start_closure)] = 0
        dfa_states.append({})
        stack = [start_closure]

        while stack:
            current = stack.pop()
            idx = dfa_map[frozenset(current)]

            for ch in charset:
                nxt = epsilon_closure(move(current, ch))
                if not nxt:
                    continue
                key = frozenset(nxt)
                if key not in dfa_map:
                    dfa_map[key] = len(dfa_states)
                    dfa_states.append({})
                    stack.append(nxt)
                dfa_states[idx][ch] = dfa_map[key]

            accepts = [s.accepting for s in current if s.accepting]
            if accepts:
                accept_map[idx] = accepts[0]

        dfa_states, accept_map = minimize_dfa(dfa_states, accept_map)

        return generate_lexer(dfa_states, accept_map)
