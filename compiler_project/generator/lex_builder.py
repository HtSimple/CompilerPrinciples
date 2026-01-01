import string
import os

###############################################################################
# 1. 基础 NFA 结构
###############################################################################

class NFAState:
    _id_counter = 0

    def __init__(self):
        self.id = NFAState._id_counter
        NFAState._id_counter += 1
        self.transitions = {}       # char -> set(states)
        self.epsilon = set()        # ε-transitions
        self.accepting = None       # (priority, name)


class NFA:
    def __init__(self, start, end):
        self.start = start
        self.end = end


###############################################################################
# 2. 正则解析器
###############################################################################

class RegexParser:
    def __init__(self, regex):
        self.regex = regex
        self.pos = 0
        self.printable = set(string.printable) - {'\n', '\r'}

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
        while self._peek() is not None and self._peek() not in ')|':
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
        while self._peek() in ('*', '+', '?'):
            op = self._next()
            s = NFAState()
            e = NFAState()
            if op == '*':
                s.epsilon |= {base.start, e}
                base.end.epsilon |= {base.start, e}
            elif op == '+':
                s.epsilon.add(base.start)
                base.end.epsilon |= {base.start, e}
            elif op == '?':
                s.epsilon |= {base.start, e}
                base.end.epsilon.add(e)
            base = NFA(s, e)
        return base

    def base(self):
        ch = self._peek()
        if ch == '(':
            self._next()
            nfa = self.expr()
            if self._peek() == ')':
                self._next()
            else:
                raise ValueError("Missing closing parenthesis")
            return nfa
        elif ch == '[':
            return self.char_class()
        elif ch == '\\':
            self._next()
            escaped_char = self._next()
            if escaped_char == 'n': escaped_char = '\n'
            elif escaped_char == 't': escaped_char = '\t'
            elif escaped_char == 'r': escaped_char = '\r' 
            return self.literal(escaped_char)
        elif ch == '.':
            self._next()
            return self.dot()
        else:
            return self.literal(self._next())

    def literal(self, ch):
        s = NFAState()
        e = NFAState()
        s.transitions.setdefault(ch, set()).add(e)
        return NFA(s, e)

    def dot(self):
        s = NFAState()
        e = NFAState()
        for c in self.printable:
            s.transitions.setdefault(c, set()).add(e)
        return NFA(s, e)

    def char_class(self):
        # === 核心修复在这里 ===
        self._next()  # skip [
        chars = set()
        while self._peek() is not None and self._peek() != ']':
            c = self._next()
            if c == '\\':
                c = self._next()
                if c == 'n': c = '\n'
                elif c == 't': c = '\t'
                elif c == 'r': c = '\r' 
                # 注意：如果还需要支持其他转义(如 \s, \d)，需要在这里扩展
            
            if self._peek() == '-':
                self._next() # skip -
                end = self._next()
                if end == '\\': # 处理范围结尾是转义的情况
                    end = self._next()
                    if end == 'n': end = '\n'
                    elif end == 't': end = '\t'
                    elif end == 'r': end = '\r'

                for x in range(ord(c), ord(end) + 1):
                    chars.add(chr(x))
            else:
                chars.add(c)
        
        if self._peek() == ']':
            self._next()
            
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
# 3. NFA -> DFA
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
# 4. DFA 最小化
###############################################################################

def minimize_dfa(dfa_states, accept_map):
    num_states = len(dfa_states)
    alphabet = set()
    for trans in dfa_states:
        alphabet |= set(trans.keys())

    partitions = {}
    for s in range(num_states):
        key = accept_map.get(s, None)
        partitions.setdefault(key, set()).add(s)
    P = list(partitions.values())

    changed = True
    while changed:
        changed = False
        new_P = []
        for group in P:
            if len(group) <= 1:
                new_P.append(group)
                continue
            splitter = {}
            for s in group:
                signature = []
                for ch in sorted(list(alphabet)):
                    target = dfa_states[s].get(ch)
                    target_group_idx = -1
                    if target is not None:
                        for i, g in enumerate(P):
                            if target in g:
                                target_group_idx = i
                                break
                    signature.append((ch, target_group_idx))
                splitter.setdefault(tuple(signature), set()).add(s)
            if len(splitter) > 1:
                changed = True
                new_P.extend(splitter.values())
            else:
                new_P.append(group)
        P = new_P

    state_map = {}
    for i, group in enumerate(P):
        for s in group:
            state_map[s] = i

    new_dfa = [{} for _ in range(len(P))]
    new_accept = {}

    for old_s, new_s in state_map.items():
        for ch, to in dfa_states[old_s].items():
            new_dfa[new_s][ch] = state_map[to]
        if old_s in accept_map:
            new_accept[new_s] = accept_map[old_s]

    return new_dfa, new_accept

###############################################################################
# 5. 生成代码
###############################################################################

def generate_lexer(dfa_states, accept_map):
    lines = []
    lines.append("import sys")
    lines.append("")
    lines.append("class Token:")
    lines.append("    def __init__(self, type_, value, line=0, col=0):")
    lines.append("        self.type = type_")
    lines.append("        self.value = value")
    lines.append("        self.line = line")
    lines.append("        self.col = col")
    lines.append("    def __repr__(self):")
    lines.append("        return f\"Token({self.type}, {self.value!r})\"")
    lines.append("")
    lines.append("class Lexer:")
    lines.append("    def __init__(self, text):")
    lines.append("        self.text = text")
    lines.append("        self.pos = 0")
    lines.append("        self.line = 1")
    lines.append("        self.col = 1")
    lines.append("")
    lines.append("    def tokenize(self):")
    lines.append("        tokens = []")
    lines.append("        while self.pos < len(self.text):")
    lines.append("            state = 0")
    lines.append("            last_accept = None")
    lines.append("            last_len = 0")
    lines.append("            current_len = 0")
    lines.append("            i = self.pos")
    lines.append("")
    lines.append("            while i < len(self.text):")
    lines.append("                char = self.text[i]")
    lines.append("                if char not in TRANS[state]:")
    lines.append("                    break")
    lines.append("                state = TRANS[state][char]")
    lines.append("                current_len += 1")
    lines.append("                i += 1")
    lines.append("                if state in ACCEPT:")
    lines.append("                    last_accept = ACCEPT[state]")
    lines.append("                    last_len = current_len")
    lines.append("")
    lines.append("            if last_accept is None:")
    lines.append("                raise SyntaxError(f\"Unexpected character at line {self.line}, col {self.col}: {self.text[self.pos]!r}\")")
    lines.append("")
    lines.append("            value = self.text[self.pos : self.pos + last_len]")
    lines.append("            lines_count = value.count('\\n')")
    lines.append("            if lines_count > 0:")
    lines.append("                self.line += lines_count")
    lines.append("                self.col = len(value) - value.rfind('\\n')")
    lines.append("            else:")
    lines.append("                self.col += len(value)")
    lines.append("            self.pos += last_len")
    lines.append("")
    lines.append("            if last_accept not in ['WS', 'SKIP', 'COMMENT', 'WHITESPACE']:")
    lines.append("                tokens.append(Token(last_accept, value, self.line, self.col))")
    lines.append("")
    lines.append("        return tokens")
    lines.append("")
    
    lines.append("TRANS = {")
    for i, trans in enumerate(dfa_states):
        if not trans: continue
        lines.append(f"    {i}: {{")
        for ch, to in trans.items():
            lines.append(f"        {repr(ch)}: {to},")
        lines.append("    },")
    lines.append("}")
    lines.append("for i in range(" + str(len(dfa_states)) + "):")
    lines.append("    if i not in TRANS: TRANS[i] = {}")
    lines.append("")
    lines.append("ACCEPT = {")
    for k, v in accept_map.items():
        lines.append(f"    {k}: {repr(v)},")
    lines.append("}")

    return "\n".join(lines)

###############################################################################
# 6. LexBuilder 主逻辑
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
                parts = line.split(None, 1)
                if len(parts) == 2:
                    rules.append((parts[0], parts[1]))

        start = NFAState()
        for index, (name, regex) in enumerate(rules):
            try:
                parser = RegexParser(regex)
                nfa = parser.parse()
                nfa.end.accepting = (index, name)
                start.epsilon.add(nfa.start)
            except Exception as e:
                raise ValueError(f"Error parsing rule '{name}': {regex}\n{e}")

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
            
            possible_accepts = [s.accepting for s in current if s.accepting is not None]
            if possible_accepts:
                best_match = min(possible_accepts, key=lambda x: x[0])
                accept_map[idx] = best_match[1]

            for ch in charset:
                nxt = epsilon_closure(move(current, ch))
                if not nxt: continue
                key = frozenset(nxt)
                if key not in dfa_map:
                    dfa_map[key] = len(dfa_states)
                    dfa_states.append({})
                    stack.append(nxt)
                dfa_states[idx][ch] = dfa_map[key]

        dfa_states, accept_map = minimize_dfa(dfa_states, accept_map)
        return generate_lexer(dfa_states, accept_map)

if __name__ == "__main__":
    # 用法：直接运行此文件生成 lexer.py
    # 请确保 rules.txt 文件存在
    try:
        builder = LexBuilder("rules.txt")
        code = builder.build()
        with open("generated_compiler/lexer.py", "w", encoding="utf-8") as f:
            f.write(code)
        print("✅ Successfully generated 'generated_compiler/lexer.py'")
    except Exception as e:
        print(f"❌ Build failed: {e}")