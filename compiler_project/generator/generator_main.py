#!/usr/bin/env python3
"""
generator_main.py
"""

import sys
import os

GEN_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(GEN_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, GEN_DIR)

from generator.lex_builder import LexBuilder
from generator.yacc_builder import YaccBuilder

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "generated_compiler")

def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def main():
    print("=" * 40)
    print("      Compiler Generator Setup")
    print("=" * 40)
    
    choice = input("请选择配置版本:\n [1] SQL\n [2] PL/0\n [3] Mini-C\n请输入 (1/2/3): ").strip()
    
    lex_filename = ""
    yacc_filename = ""

    if choice == '1':
        lex_filename = "lex_rules_1.lex"
        yacc_filename = "yacc_rules_1.bnf"
        print("👉 已选择: SQL (rules_1)")
    elif choice == '2':
        lex_filename = "lex_rules_2.lex"
        yacc_filename = "yacc_rules_2.bnf"
        print("👉 已选择: PL/0 (rules_2)")
    elif choice == '3':
        lex_filename = "lex_rules_3.lex"
        yacc_filename = "yacc_rules_3.bnf"
        print("👉 已选择: Mini-C (rules_3)")
    else:
        print(f"❌ 输入错误: '{choice}'。")
        sys.exit(1)

    LEX_RULES = os.path.join(PROJECT_ROOT, "config", lex_filename)
    YACC_RULES = os.path.join(PROJECT_ROOT, "config", yacc_filename)

    if not os.path.exists(LEX_RULES) or not os.path.exists(YACC_RULES):
        print(f"❌ 错误：找不到配置文件。\n {LEX_RULES}\n {YACC_RULES}")
        sys.exit(1)

    ensure_output_dir()

    print(f"\n[A] 生成 lexer.py (from {lex_filename})...")
    lex_builder = LexBuilder(LEX_RULES)
    with open(os.path.join(OUTPUT_DIR, "lexer.py"), "w", encoding="utf-8") as f:
        f.write(lex_builder.build())

    print(f"[B] 生成 parser.py (from {yacc_filename})...")
    yacc_builder = YaccBuilder(YACC_RULES)
    yacc_builder.run(out_path=os.path.join(OUTPUT_DIR, "parser.py"))

    print("\n🎉 编译器生成完成！")

if __name__ == "__main__":
    main()