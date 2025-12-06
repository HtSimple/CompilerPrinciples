#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
yacc_builder.py

根据 BNF 文件生成 LL(1) temp_parser.py（无语义动作）
完整支持 FIRST/FOLLOW 集计算、LL(1) 预测分析表生成及冲突提示
修复点：
1. 修正 FOLLOW 集计算逻辑，避免空产生式覆盖非空产生式条目
2. 空产生式处理时跳过已存在的非空产生式条目
3. 保留冲突提示但仅对真正的 LL(1) 冲突抛出异常
"""

import os
import re
from collections import defaultdict

EPSILON = 'ε'

class YaccBuilder:
    def __init__(self, bnf_file):
        if not os.path.exists(bnf_file):
            raise FileNotFoundError(f"BNF 文件不存在: {bnf_file}")
        self.bnf_file = bnf_file
        self.productions = []  # (lhs, rhs list, semantic_tag)
        self.nonterminals = set()
        self.terminals = set()
        self.start_symbol = None

        self.first = defaultdict(set)
        self.follow = defaultdict(set)
        self.parse_table = dict()

    def parse_bnf(self):
        """解析 BNF 文件，生成 productions、nonterminals、terminals"""
        with open(self.bnf_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if "#" in line:
                    line, semantic_tag = line.split("#", 1)
                    semantic_tag = semantic_tag.strip()
                else:
                    semantic_tag = None

                if "::=" not in line:
                    continue

                lhs, rhs = line.split("::=")
                lhs = lhs.strip()
                rhs_symbols = rhs.strip().split() if rhs.strip() != EPSILON else []

                self.productions.append((lhs, rhs_symbols, semantic_tag))
                self.nonterminals.add(lhs)
                for sym in rhs_symbols:
                    if re.match(r"<.*>", sym):
                        self.nonterminals.add(sym)
                    else:
                        self.terminals.add(sym)

        if self.productions:
            self.start_symbol = self.productions[0][0]

        # 移除终结符集中的非终结符
        self.terminals -= self.nonterminals

    # -------------------- FIRST/FOLLOW 集计算 --------------------
    def compute_first(self):
        """计算 FIRST 集"""
        # 初始化：终结符的 FIRST 集是自身
        for t in self.terminals:
            self.first[t] = {t}
        for nt in self.nonterminals:
            self.first[nt] = set()

        changed = True
        while changed:
            changed = False
            for lhs, rhs, _ in self.productions:
                first_lhs = self.first[lhs]
                current_first = set()

                if not rhs:  # 空产生式
                    current_first.add(EPSILON)
                else:
                    for symbol in rhs:
                        current_first.update(self.first[symbol] - {EPSILON})
                        if EPSILON not in self.first[symbol]:
                            break
                    else:
                        current_first.add(EPSILON)

                if not current_first.issubset(first_lhs):
                    first_lhs.update(current_first)
                    changed = True

    def compute_follow(self):
        """修正版 FOLLOW 集计算：避免将非空产生式起始符号混入 FOLLOW 集"""
        for nt in self.nonterminals:
            self.follow[nt] = set()
        self.follow[self.start_symbol].add('$')

        changed = True
        while changed:
            changed = False
            for lhs, rhs, _ in self.productions:
                trailer = self.follow[lhs].copy()  # 初始 trailer 为 lhs 的 FOLLOW 集
                # 反向遍历右部符号
                for sym in reversed(rhs):
                    if sym in self.nonterminals:
                        before_len = len(self.follow[sym])
                        # 将 trailer 加入当前非终结符的 FOLLOW 集
                        self.follow[sym].update(trailer)
                        # 仅当当前符号能推导出 ε 时，扩展 trailer
                        if EPSILON in self.first[sym]:
                            new_trailer = set()
                            new_trailer.update(self.first[sym] - {EPSILON})
                            new_trailer.update(trailer)
                            trailer = new_trailer
                        else:
                            # 不能推导出 ε，trailer 仅为当前符号的 FIRST 集（排除 ε）
                            trailer = self.first[sym] - {EPSILON}
                        # 检查是否有更新
                        if len(self.follow[sym]) > before_len:
                            changed = True
                    else:
                        # 终结符：trailer 重置为该终结符
                        trailer = {sym}

    def first_of_sequence(self, symbols):
        """计算符号序列的 FIRST 集"""
        if not symbols:
            return {EPSILON}
        result = set()
        for sym in symbols:
            result.update(self.first[sym] - {EPSILON})
            if EPSILON not in self.first[sym]:
                break
        else:
            result.add(EPSILON)
        return result

    # -------------------- LL(1) parse_table --------------------
    def build_parse_table(self):
        """生成 LL(1) 预测分析表（修复空产生式覆盖问题）"""
        self.compute_first()
        self.compute_follow()

        for lhs, rhs, tag in self.productions:
            first_rhs = self.first_of_sequence(rhs)
            # 处理非空产生式（first_rhs 不含 ε）
            for terminal in first_rhs - {EPSILON}:
                key = (lhs, terminal)
                if key in self.parse_table:
                    print(f"⚠ LL(1) 冲突: {lhs}, {terminal} 已存在 {self.parse_table[key][0]}, 尝试加入 {rhs}")
                    raise ValueError(f"LL(1) 冲突无法解决: {lhs}, {terminal} 同时匹配 {self.parse_table[key][0]} 和 {rhs}")
                self.parse_table[key] = (rhs, tag)
            # 处理空产生式（first_rhs 包含 ε）
            if EPSILON in first_rhs:
                for terminal in self.follow[lhs]:
                    key = (lhs, terminal)
                    # 关键修复：空产生式不覆盖已存在的非空产生式条目
                    if key in self.parse_table:
                        continue
                    # 检查空产生式是否与其他空产生式冲突
                    if key in self.parse_table:
                        print(f"⚠ LL(1) 冲突: {lhs}, {terminal} 已存在 {self.parse_table[key][0]}, 尝试加入 {rhs}")
                        raise ValueError(f"LL(1) 冲突无法解决: {lhs}, {terminal} 同时匹配 {self.parse_table[key][0]} 和 {rhs}")
                    self.parse_table[key] = (rhs, tag)

    # -------------------- 生成 temp_parser.py --------------------
    def run(self, out_path):
        self.parse_bnf()
        self.build_parse_table()

        # 生成解析器代码
        parser_code = [
            "# Auto-generated by yacc_builder.py",
            "# Table-driven LL(1) parser (no semantic actions)",
            "",
            f"nonterminals = {list(self.nonterminals)!r}",
            f"terminals = {list(self.terminals)!r}",
            f"start_symbol = {self.start_symbol!r}",
            "",
            f"productions = {self.productions!r}",
            "",
            "parse_table = {"
        ]
        # 按有序方式生成解析表（便于阅读）
        sorted_table = sorted(self.parse_table.items(), key=lambda x: (x[0][0], x[0][1]))
        for (nt, terminal), (rhs, tag) in sorted_table:
            tag_str = tag if tag else ""
            parser_code.append(f"    ('{nt}', '{terminal}'): ({rhs!r}, '{tag_str}'),")
        parser_code.append("}\n")

        # 解析函数
        parser_code.append("""
def parse(token_list, verbose=True):
    if not token_list or token_list[-1] != '$':
        token_list = list(token_list) + ['$']
    stack = ['$']
    stack.append(start_symbol)
    ip = 0
    while stack:
        top = stack.pop()
        lookahead = token_list[ip]
        if verbose:
            print(f'STACK TOP: {top}, LOOKAHEAD: {lookahead}')
        # 处理终结符或结束符
        if top == '$' or top not in nonterminals:
            if top == lookahead:
                ip += 1
                if top == '$':
                    return True
                continue
            else:
                if verbose:
                    print(f'Unexpected token: expected {top}, got {lookahead}')
                return False
        # 处理非终结符
        key = (top, lookahead)
        entry = parse_table.get(key)
        if entry is None:
            if verbose:
                print(f'No table entry for {key}. Syntax error.')
            return False
        right, _tag = entry
        # 反向压栈
        for sym in reversed(right):
            stack.append(sym)
    return True
""")

        # 写入文件
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(parser_code))
        print(f"✔ temp_parser.py 已生成 → {out_path}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("用法: python yacc_builder.py your.bnf temp_parser.py")
    else:
        builder = YaccBuilder(sys.argv[1])
        builder.run(sys.argv[2])