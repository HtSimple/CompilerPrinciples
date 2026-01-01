#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
yacc_builder.py

从 BNF 文法自动构造 LL(1) 预测分析表，
并生成 temp_parser.py（支持语义动作注入）
"""

from collections import defaultdict
import os

EPSILON = 'ε'
ENDMARK = '$'
REDUCE_MARK = '@REDUCE@'


class YaccBuilder:
    def __init__(self, bnf_file):
        self.bnf_file = bnf_file

        self.productions = defaultdict(list)
        self.nonterminals = set()
        self.terminals = set()

        self.first = defaultdict(set)
        self.follow = defaultdict(set)
        self.table = dict()

        self.start_symbol = None



    # --------------------------------------------------
    # 读取 BNF 文法
    # --------------------------------------------------
    def load_grammar(self):
        if not os.path.exists(self.bnf_file):
            raise FileNotFoundError(self.bnf_file)

        lines = []
        with open(self.bnf_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "#" in line:
                    line = line[:line.index("#")].strip()
                lines.append(line)

        i = 0
        while i < len(lines):
            line = lines[i]
            if "::=" not in line:
                i += 1
                continue

            lhs, rhs = line.split("::=", 1)
            lhs = lhs.strip()

            if self.start_symbol is None:
                self.start_symbol = lhs

            self.nonterminals.add(lhs)

            rhs_all = rhs.strip()
            i += 1
            while i < len(lines) and "::=" not in lines[i]:
                rhs_all += " " + lines[i]
                i += 1

            current = []
            for tok in rhs_all.split():
                if tok == "|":
                    self.productions[lhs].append(current)
                    current = []
                else:
                    if tok in ("ε", "EPSILON"):
                        tok = EPSILON
                    current.append(tok)

            self.productions[lhs].append(current)

        for A, prods in self.productions.items():
            for prod in prods:
                for sym in prod:
                    if sym != EPSILON and not self.is_nonterminal(sym):
                        self.terminals.add(sym)

        self.terminals.add(ENDMARK)

    def is_nonterminal(self, sym):
        return sym.startswith("<") and sym.endswith(">")

    # --------------------------------------------------
    # FIRST（标准算法）
    # --------------------------------------------------
    def compute_first(self):
        for t in self.terminals:
            self.first[t] = {t}

        for nt in self.nonterminals:
            self.first[nt] = set()

        changed = True
        while changed:
            changed = False
            for A, prods in self.productions.items():
                for prod in prods:
                    before = len(self.first[A])
                    self.first[A] |= self.first_of_string(prod)
                    if len(self.first[A]) > before:
                        changed = True

    # --------------------------------------------------
    # FOLLOW（标准算法）
    # --------------------------------------------------
    def compute_follow(self):
        self.follow[self.start_symbol].add(ENDMARK)

        changed = True
        while changed:
            changed = False
            for A, prods in self.productions.items():
                for prod in prods:
                    for i, B in enumerate(prod):
                        if not self.is_nonterminal(B):
                            continue
                        beta = prod[i + 1:]
                        first_beta = self.first_of_string(beta)

                        before = len(self.follow[B])
                        self.follow[B] |= (first_beta - {EPSILON})

                        if EPSILON in first_beta or not beta:
                            self.follow[B] |= self.follow[A]

                        if len(self.follow[B]) > before:
                            changed = True

    # --------------------------------------------------
    # FIRST(α)
    # --------------------------------------------------
    def first_of_string(self, symbols):
        result = set()
        for sym in symbols:
            if sym == EPSILON:
                result.add(EPSILON)
                return result
            result |= (self.first[sym] - {EPSILON})
            if EPSILON not in self.first[sym]:
                return result
        result.add(EPSILON)
        return result

    # --------------------------------------------------
    # 构造 LL(1) 表（含 start symbol 兜底）
    # --------------------------------------------------
    def build_table(self):
        for A, prods in self.productions.items():
            for prod in prods:
                first_alpha = self.first_of_string(prod)
                for t in first_alpha - {EPSILON}:
                    self.table[(A, t)] = prod
                if EPSILON in first_alpha:
                    for b in self.follow[A]:
                        self.table[(A, b)] = prod

        # ✅ 起始符 FIRST 强制补全（PL/0 必需）
        for prod in self.productions[self.start_symbol]:
            for t in self.first_of_string(prod) - {EPSILON}:
                self.table[(self.start_symbol, t)] = prod

    # --------------------------------------------------
    # 生成 parser（REDUCE 原子化）
    # --------------------------------------------------
    def generate_parser(self, out_path):
        lines = [
            "#!/usr/bin/env python3",
            "# -*- coding: utf-8 -*-",
            "",
            "from collections import deque",
            "from generator.action_builder import TAC_OUTPUT_FILE",
            "",
            "ACTIONS = {}  # 将由 ActionBuilder 注入",
            "",
            "def parse(tokens, verbose=False):",
            "    token_types = [t.type for t in tokens] + ['$']",
            "    value_stack = []",
            "",
            f"    stack = deque(['$', '{self.start_symbol}'])",
            "    i = 0",
            "",
            "    while stack:",
            "        top = stack.pop()",
            "        lookahead = token_types[i]",
            "",
            "        if top == lookahead == '$':",
            "            return value_stack[-1] if value_stack else None",
            "",
            "        if isinstance(top, tuple) and top[0] == '@REDUCE@':",
            "            _, lhs, rhs = top",
            "            if rhs != ['ε']:",
            "                children = value_stack[-len(rhs):]",
            "                del value_stack[-len(rhs):]",
            "            else:",
            "                children = []",
            "",
            "            key = f\"{lhs} -> {' '.join(rhs)}\"",
            "            node = ACTIONS[key](children) if key in ACTIONS else None",
            "            value_stack.append(node)",
            "            continue",
            "",
            "        if not top.startswith('<'):",
            "            if top == lookahead:",
            "                value_stack.append(tokens[i])",
            "                i += 1",
            "                continue",
            "            raise SyntaxError(f'期望 {top}, 得到 {lookahead}')",
            "",
            "        key = (top, lookahead)",
            "        if key not in PARSE_TABLE:",
            "            raise SyntaxError(f'分析表无条目: {key}')",
            "",
            "        prod = PARSE_TABLE[key]",
            "        stack.append(('@REDUCE@', top, prod))",
            "        for sym in reversed(prod):",
            "            if sym != 'ε':",
            "                stack.append(sym)",
            "",
            "    return None",
            "",
            "PARSE_TABLE = {"
        ]

        for (A, t), prod in sorted(self.table.items()):
            lines.append(f"    ({A!r}, {t!r}): {prod!r},")

        lines += ["}"]

        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"✓ temp_parser.py 已生成 -> {out_path}")

    # --------------------------------------------------
    def run(self, out_path):
        self.load_grammar()
        self.compute_first()
        self.compute_follow()
        self.build_table()
        self.generate_parser(out_path)


if __name__ == "__main__":
    import sys
    YaccBuilder(sys.argv[1]).run(sys.argv[2])
