#!/usr/bin/env python3
"""
test_compiler.py - 支持 SQL, PL/0, Mini-C
"""

import sys
import os
import glob
from dataclasses import dataclass

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(TEST_DIR, ".."))
sys.path.append(PROJECT_ROOT)

try:
    from generated_compiler.lexer import Lexer, Token
    from generated_compiler.parser import parse
except ImportError as e:
    print("❌ 无法导入 generated_compiler。请先运行 generator_main.py")
    sys.exit(1)

# =========================================================
# 通用工具
# =========================================================

def load_batch_files(pattern):
    path = os.path.join(TEST_DIR, pattern)
    files = glob.glob(path)
    files.sort()
    loaded = {}
    print(f"\n📂 扫描路径: {TEST_DIR} ({pattern})")
    if not files: return {}
    for fpath in files:
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                loaded[os.path.basename(fpath)] = f.read()
        except: pass
    return loaded

def print_lex_trace(tokens):
    print(f"\n   [1. 词法分析 (Lex Trace)]")
    print(f"   {'ID':<4}| {'Line':<5}| {'Type':<15}| {'Value'}")
    print("   " + "-" * 50)
    for i, t in enumerate(tokens):
        val = str(t.value).replace('\n','\\n')
        if len(val)>20: val = val[:17]+"..."
        print(f"   {i:<4}| {getattr(t,'line','?'):<5}| {t.type:<15}| {val}")

@dataclass
class AstNode:
    type: str; name: str; context: str; line: int; extra: str

# =========================================================
# 1. SQL 逻辑
# =========================================================
def extract_sql_structures(tokens):
    nodes = []
    line = 1
    for i, tok in enumerate(tokens):
        if hasattr(tok, 'line'): line = tok.line
        if tok.type == "SELECT":
            nodes.append(AstNode("SELECT", "Query", "Batch", line, "字段提取..."))
        elif tok.type == "INSERT":
            nodes.append(AstNode("INSERT", "Table", "Batch", line, ""))
    return nodes

def summary_sql(nodes):
    return "\n".join([f"  └── [{n.line}] {n.type} {n.extra}" for n in nodes])

# =========================================================
# 2. PL/0 逻辑
# =========================================================
def extract_pl0_structures(tokens):
    nodes = []
    scope = "Global"; line = 1; i = 0
    while i < len(tokens):
        t = tokens[i]
        if hasattr(t, 'line'): line = t.line
        if t.type == "PROCEDURE":
            if i+1 < len(tokens): 
                scope = tokens[i+1].value
                nodes.append(AstNode("PROCEDURE", scope, "Global", line, ""))
        elif t.type == "VAR" and i+1 < len(tokens) and tokens[i+1].type=="IDENTIFIER":
             nodes.append(AstNode("VAR", tokens[i+1].value, scope, line, ""))
        i += 1
    return nodes

def summary_pl0(nodes):
    return "\n".join([f"  └── [{n.context}] {n.type}: {n.name}" for n in nodes])

# =========================================================
# 3. Mini-C 逻辑
# =========================================================
def extract_c_structures(tokens):
    nodes = []
    current_func = "Global"
    line = 1
    i = 0
    
    while i < len(tokens):
        t = tokens[i]
        if hasattr(t, 'line'): line = t.line

        # 识别函数定义: Type + ID + (
        if t.type in ("INT", "FLOAT", "VOID"):
            if i+2 < len(tokens) and tokens[i+1].type == "IDENTIFIER" and tokens[i+2].type == "LPAREN":
                # 这是一个函数定义 
                func_name = tokens[i+1].value
                current_func = func_name
                nodes.append(AstNode("Function Def", func_name, "Global", line, f"Ret: {t.value}"))
                i += 2; continue
            
            # 识别变量声明: Type + ID + ;
            elif i+2 < len(tokens) and tokens[i+1].type == "IDENTIFIER" and tokens[i+2].type == "SEMI":
                var_name = tokens[i+1].value
                nodes.append(AstNode("Var Decl", var_name, current_func, line, f"Type: {t.value}"))
                i += 2; continue

        # 控制流 IF/WHILE
        if t.type in ("IF", "WHILE"):
            nodes.append(AstNode("Control Flow", t.type, current_func, line, ""))
        
        if t.type == "RETURN":
            val = "void"
            if i+1 < len(tokens) and tokens[i+1].type != "SEMI":
                val = "expr"
            nodes.append(AstNode("Return", val, current_func, line, ""))

        i += 1
    return nodes

def summary_c(nodes):
    lines = ["Mini-C Structure Tree"]
    for n in nodes:
        lines.append(f"  └── [{n.context}] {n.type}: {n.name}  {n.extra}")
    return "\n".join(lines)

# =========================================================
# 运行引擎
# =========================================================
def run_suite(mode, pattern, extractor, summarizer, default_code):
    cases = load_batch_files(pattern)
    if not cases: cases = {"Default": default_code}

    print(f"\n🚀 正在运行 {mode} 测试")
    print("="*60)

    for fname, code in cases.items():
        print(f"\n📄 文件: {fname}")
        print("-" * 40)
        print(f"  > {code.splitlines()[0]} ...")

        try:
            # 1. Lex
            lexer = Lexer(code)
            tokens = lexer.tokenize()
            print_lex_trace(tokens)

            # 2. Parse
            print("\n   [2. 语法分析]")
            print("   " + "."*40)
            token_types = [t.type for t in tokens]
            # SQL 不需要结束符，PL/0 和 C 可能需要 EOF 标记，这里视文法而定
            # 为了通用性，如果 generator 支持，通常加 $
            if mode != 'SQL': token_types.append('$') 

            success = parse(token_types, verbose=True)
            print("   " + "."*40)

            if success:
                print("   ✅ 解析成功")
                print("\n   [3. 语义提取]")
                nodes = extractor(tokens)
                print(summarizer(nodes))
            else:
                print("   ❌ 解析失败")
                if "false" in fname or "error" in fname:
                    print("      ✨ (提示: 预期内的错误)")

        except Exception as e:
            print(f"   ❌ 异常: {e}")

if __name__ == "__main__":
    print("Compiler Test Suite")
    print(" [1] SQL\n [2] PL/0\n [3] Mini-C")
    c = input("选择: ").strip()
    
    if c == '1':
        run_suite("SQL", "sql_test_code*.txt", extract_sql_structures, summary_sql, "SELECT * FROM t;")
    elif c == '2':
        run_suite("PL/0", "PL0_test_code*.txt", extract_pl0_structures, summary_pl0, "var a; begin a:=1; end.")
    elif c == '3':
        # 默认 C 代码
        default_c = "int main() { int a; a = 10; return a; }"
        run_suite("Mini-C", "C_test_code*.txt", extract_c_structures, summary_c, default_c)
    else:
        print("Invalid")