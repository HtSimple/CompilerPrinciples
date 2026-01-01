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
        self.transitions = {}  # char -> set(states)
        self.epsilon = set()  # ε-transitions
        self.accepting = None  # token type


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
    - 简单转义：\t, \n, \r
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
        if ch == '\\':  # 处理转义字符
            self._next()  # 跳过\
            escaped = self._next()
            if escaped == 't':
                ch = '\t'
            elif escaped == 'n':
                ch = '\n'
            elif escaped == 'r':
                ch = '\r'
            else:
                ch = escaped
            return self.literal(ch)
        elif ch == '(':
            self._next()
            nfa = self.expr()
            if self._peek() != ')':
                raise ValueError("Missing closing parenthesis")
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
        negate = False

        # 检查是否是否定字符类
        if self._peek() == '^':
            self._next()
            negate = True

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

        if negate:
            # 对于否定字符类，创建所有字符（简化处理）
            all_chars = set(chr(i) for i in range(32, 127))  # 可打印字符
            chars = all_chars - chars

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
    if not dfa_states:
        return [], {}

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
                for ch in sorted(alphabet):  # 按字母顺序排序确保一致性
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
            if to in state_map:
                new_dfa[new_s][ch] = state_map[to]

        if old_s in accept_map:
            new_accept[new_s] = accept_map[old_s]

    return new_dfa, new_accept


###############################################################################
# 生成 lexer.py（修复关键字处理）
###############################################################################

def generate_lexer(dfa_states, accept_map, keywords):
    """
    生成词法分析器代码

    Args:
        dfa_states: DFA 状态转移表
        accept_map: 接受状态映射
        keywords: 关键字字典 {keyword_text: TOKEN_TYPE}
    """
    lines = []

    lines.append("class Token:")
    lines.append("    def __init__(self, type_, value):")
    lines.append("        self.type = type_")
    lines.append("        self.value = value")
    lines.append("    def __repr__(self):")
    lines.append("        return f\"Token({self.type}, {repr(self.value)})\"")
    lines.append("")

    # 生成关键字映射
    lines.append("# 关键字映射")
    lines.append("KEYWORDS = {")
    for kw_text, kw_type in sorted(keywords.items()):
        lines.append(f"    {repr(kw_text)}: {repr(kw_type)},")
    lines.append("}")
    lines.append("")

    lines.append("class Lexer:")
    lines.append("    def __init__(self, text):")
    lines.append("        self.text = text")
    lines.append("        self.pos = 0")
    lines.append("")
    lines.append("    def tokenize(self):")
    lines.append("        tokens = []")
    lines.append("        while self.pos < len(self.text):")
    lines.append("            # 跳过空白")
    lines.append("            if self.text[self.pos] in ' \\t\\r\\n':")
    lines.append("                self.pos += 1")
    lines.append("                continue")
    lines.append("")
    lines.append("            state = 0")
    lines.append("            last_accept = None")
    lines.append("            last_pos = self.pos")
    lines.append("            i = self.pos")
    lines.append("")
    lines.append("            while i < len(self.text):")
    lines.append("                ch = self.text[i]")
    lines.append("                if state in TRANS and ch in TRANS[state]:")
    lines.append("                    state = TRANS[state][ch]")
    lines.append("                    i += 1")
    lines.append("                    if state in ACCEPT:")
    lines.append("                        last_accept = ACCEPT[state]")
    lines.append("                        last_pos = i")
    lines.append("                else:")
    lines.append("                    break")
    lines.append("")
    lines.append("            if last_accept is None:")
    lines.append(
        "                raise SyntaxError(f\"Illegal character: {self.text[self.pos]!r} at position {self.pos}\")")
    lines.append("")
    lines.append("            value = self.text[self.pos:last_pos]")
    lines.append("            self.pos = last_pos")
    lines.append("")
    lines.append("            # 跳过空白和注释")
    lines.append("            if last_accept in ('WS', 'COMMENT'):")
    lines.append("                continue")
    lines.append("")
    lines.append("            # 关键字识别（动态）")
    lines.append("            tok_type = last_accept")
    lines.append("            if tok_type == 'IDENTIFIER' and value in KEYWORDS:")
    lines.append("                tok_type = KEYWORDS[value]")
    lines.append("")
    lines.append("            tokens.append(Token(tok_type, value))")
    lines.append("")
    lines.append("        # 添加结束标记")
    lines.append("        tokens.append(Token('$', '$'))")
    lines.append("        return tokens")
    lines.append("")

    lines.append("TRANS = {")
    for i, trans in enumerate(dfa_states):
        lines.append(f"    {i}: {{")
        for ch, to in sorted(trans.items()):  # 排序确保输出一致
            lines.append(f"        {repr(ch)}: {to},")
        lines.append("    },")
    lines.append("}")
    lines.append("")
    lines.append("ACCEPT = {")
    for k, v in sorted(accept_map.items()):
        lines.append(f"    {k}: {repr(v)},")
    lines.append("}")

    return "\n".join(lines)


###############################################################################
# LexBuilder（修复关键字提取和字符集）
###############################################################################

class LexBuilder:
    def __init__(self, lex_rules_path: str):
        self.lex_rules_path = lex_rules_path

    def build(self) -> str:
        rules = []
        keywords = {}  # {keyword_text: TOKEN_TYPE}
        pl0_chars = set()  # PL/0使用的字符集

        with open(self.lex_rules_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("---"):
                    continue

                parts = line.split(None, 1)
                if len(parts) != 2:
                    continue

                name, regex = parts
                rules.append((name, regex))

                # 收集关键字（从正则中提取关键字文本）
                if name in ['CONST', 'VAR', 'PROCEDURE', 'CALL', 'BEGIN', 'END',
                            'IF', 'THEN', 'WHILE', 'DO', 'ODD']:
                    # 关键字的正则通常是关键字本身
                    kw_text = regex.strip('"\'')  # 移除可能的引号
                    keywords[kw_text] = name

                # 收集字符集
                if name == 'IDENTIFIER':
                    pl0_chars.update(string.ascii_letters + string.digits)
                elif name == 'NUMBER':
                    pl0_chars.update(string.digits)
                elif name in ['PLUS', 'MINUS', 'MULT', 'DIV']:
                    pl0_chars.update('+-*/')
                elif name in ['LT', 'GT', 'LE', 'GE', 'EQ', 'NE', 'ASSIGN']:
                    pl0_chars.update('<>#=:')
                elif name in ['LPAREN', 'RPAREN', 'COMMA', 'SEMI', 'DOT']:
                    pl0_chars.update('(),;.')
                elif name in ['CONST', 'VAR', 'PROCEDURE', 'CALL', 'BEGIN', 'END',
                              'IF', 'THEN', 'WHILE', 'DO', 'ODD']:
                    # 关键字由字母组成
                    for ch in regex.strip('"\''):
                        pl0_chars.add(ch)

        # 确保包含空白字符
        pl0_chars.update(' \t\r\n')

        # 构建NFA
        start = NFAState()

        for name, regex in rules:
            try:
                # 处理WS特殊规则
                if name == 'WS':
                    # 为空白创建简单的NFA
                    s = NFAState()
                    e = NFAState()
                    e.accepting = 'WS'
                    for ch in ' \t\r\n':
                        s.transitions.setdefault(ch, set()).add(e)
                    start.epsilon.add(s)
                else:
                    parser = RegexParser(regex)
                    nfa = parser.parse()
                    nfa.end.accepting = name
                    start.epsilon.add(nfa.start)
            except Exception as e:
                print(f"警告：解析正则 '{regex}' 时出错: {e}")
                continue

        # 构建DFA（使用PL/0字符集）
        dfa_states = []
        dfa_map = {}
        accept_map = {}

        start_closure = epsilon_closure({start})
        if not start_closure:
            raise ValueError("NFA构建失败：起始状态闭包为空")

        dfa_map[frozenset(start_closure)] = 0
        dfa_states.append({})
        stack = [start_closure]

        while stack:
            current = stack.pop()
            idx = dfa_map[frozenset(current)]

            for ch in pl0_chars:
                nxt = epsilon_closure(move(current, ch))
                if not nxt:
                    continue

                key = frozenset(nxt)
                if key not in dfa_map:
                    dfa_map[key] = len(dfa_states)
                    dfa_states.append({})
                    stack.append(nxt)
                dfa_states[idx][ch] = dfa_map[key]

            # 选择接受状态（如果有多个，选择优先级最高的）
            accepts = [s.accepting for s in current if s.accepting]
            if accepts:
                # 优先级：关键字 > 标识符 > 其他
                priority_order = ['CONST', 'VAR', 'PROCEDURE', 'CALL', 'BEGIN', 'END',
                                  'IF', 'THEN', 'WHILE', 'DO', 'ODD', 'IDENTIFIER']
                for token_type in priority_order:
                    if token_type in accepts:
                        accept_map[idx] = token_type
                        break
                else:
                    accept_map[idx] = accepts[0]

        # 最小化DFA
        dfa_states, accept_map = minimize_dfa(dfa_states, accept_map)

        return generate_lexer(dfa_states, accept_map, keywords)