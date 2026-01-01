#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
from collections import defaultdict

EPSILON = 'ε'

class YaccBuilder:
    def __init__(self, bnf_file):
        if not os.path.exists(bnf_file):
            raise FileNotFoundError(f"BNF 文件不存在: {bnf_file}")
        self.bnf_file = bnf_file
        self.productions = []
        self.nonterminals = set()
        self.terminals = set()
        self.start_symbol = None
        self.first = defaultdict(set)
        self.follow = defaultdict(set)
        self.parse_table = dict()

    def parse_bnf(self):
        with open(self.bnf_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                if "#" in line: line, tag = line.split("#", 1)
                else: tag = None
                if "::=" not in line: continue
                lhs, rhs = line.split("::=")
                lhs = lhs.strip()
                rhs_syms = rhs.strip().split() if rhs.strip() != EPSILON else []
                self.productions.append((lhs, rhs_syms, tag.strip() if tag else None))
                self.nonterminals.add(lhs)
                for s in rhs_syms:
                    if re.match(r"<.*>", s): self.nonterminals.add(s)
                    else: self.terminals.add(s)
        if self.productions: self.start_symbol = self.productions[0][0]
        self.terminals -= self.nonterminals

    # FIRST 集计算 ===
    def compute_first(self):
        for t in self.terminals: self.first[t] = {t}
        for nt in self.nonterminals: self.first[nt] = set()
        
        changed = True
        while changed:
            changed = False
            for lhs, rhs, _ in self.productions:
                # 计算右部序列的 FIRST
                seq_first = set()
                all_nullable = True
                
                if not rhs: # 空产生式
                    seq_first = {EPSILON}
                else:
                    for sym in rhs:
                        sym_first = self.first[sym]
                        seq_first.update(sym_first - {EPSILON})
                        if EPSILON not in sym_first:
                            all_nullable = False
                            break
                    if all_nullable:
                        seq_first.add(EPSILON)

                # 更新 LHS 的 FIRST
                if not seq_first.issubset(self.first[lhs]):
                    self.first[lhs].update(seq_first)
                    changed = True

    # 序列 FIRST 计算 ===
    def first_of_sequence(self, symbols):
        result = set()
        all_nullable = True
        if not symbols: return {EPSILON}
        
        for sym in symbols:
            result.update(self.first[sym] - {EPSILON})
            if EPSILON not in self.first[sym]:
                all_nullable = False
                break
        if all_nullable:
            result.add(EPSILON)
        return result

    def compute_follow(self):
        for nt in self.nonterminals: self.follow[nt] = set()
        self.follow[self.start_symbol].add('$')
        changed = True
        while changed:
            changed = False
            for lhs, rhs, _ in self.productions:
                trailer = self.follow[lhs].copy()
                for sym in reversed(rhs):
                    if sym in self.nonterminals:
                        before = len(self.follow[sym])
                        self.follow[sym].update(trailer)
                        if EPSILON in self.first[sym]: trailer.update(self.first[sym] - {EPSILON})
                        else: trailer = self.first[sym] - {EPSILON}
                        if len(self.follow[sym]) > before: changed = True
                    else: trailer = {sym}

    def build_parse_table(self):
        self.compute_first()
        self.compute_follow()
        for lhs, rhs, tag in self.productions:
            first_rhs = self.first_of_sequence(rhs)
            for t in first_rhs - {EPSILON}:
                self.add_entry(lhs, t, rhs, tag)
            if EPSILON in first_rhs:
                for t in self.follow[lhs]:
                    self.add_entry(lhs, t, rhs, tag)

    def add_entry(self, lhs, term, rhs, tag):
        key = (lhs, term)
        if key in self.parse_table:
            # 优先保留非空产生式
            old_rhs = self.parse_table[key][0]
            if not old_rhs and rhs: self.parse_table[key] = (rhs, tag)
        else:
            self.parse_table[key] = (rhs, tag)

    def run(self, out_path):
        self.parse_bnf()
        self.build_parse_table()
        
        code = [
            "nonterminals = " + str(list(self.nonterminals)),
            "terminals = " + str(list(self.terminals)),
            "start_symbol = " + repr(self.start_symbol),
            "parse_table = {"
        ]
        for k, v in sorted(self.parse_table.items()):
            tag = v[1] if v[1] else ""
            code.append(f"    {k}: ({v[0]!r}, '{tag}'),")
        code.append("}")
        
        # 写入标准的 parse 函数
        code.append("""
def parse(token_list, verbose=True):
    if not token_list or token_list[-1] != '$':
        token_list = list(token_list) + ['$']
    stack = ['$']
    stack.append(start_symbol)
    ip = 0
    while stack:
        top = stack.pop()
        lookahead = token_list[ip]
        if verbose: print(f'STACK TOP: {top}, LOOKAHEAD: {lookahead}')
        
        if top == '$': return True if lookahead == '$' else False
        
        if top not in nonterminals:
            if top == lookahead: ip += 1
            else: 
                if verbose: print(f'Error: Expected {top}, got {lookahead}')
                return False
        else:
            key = (top, lookahead)
            if key not in parse_table:
                if verbose: print(f'No table entry for {key}')
                return False
            rhs, _ = parse_table[key]
            for sym in reversed(rhs): stack.append(sym)
    return True
""")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f: f.write("\n".join(code))
        print(f"✔ Parser 已更新: {out_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3: print("Usage: python yacc_builder.py <bnf> <out>")
    else: YaccBuilder(sys.argv[1]).run(sys.argv[2])