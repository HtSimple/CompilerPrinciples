#!/usr/bin/env python3
"""
generator_main.py

Compiler Generator 主入口
依次执行：
1️⃣ 生成 lexer.py
2️⃣ 生成 temp_parser.py（无语义动作）
3️⃣ 注入语义动作，生成最终 parser.py
"""

import sys
import os

# ---------------------------------------------------------
# 1. 找到项目根目录：compiler_project/
# ---------------------------------------------------------
GEN_DIR = os.path.dirname(os.path.abspath(__file__))              # compiler_project/generator
PROJECT_ROOT = os.path.abspath(os.path.join(GEN_DIR, ".."))       # compiler_project/

# ---------------------------------------------------------
# 2. 修复 Python 搜索路径（非常关键）
# ---------------------------------------------------------
# 确保可以导入：
#   generator.lex_builder
#   generator.yacc_builder
#   generator.action_builder
#   config.lex_rules.lex
#   config.yacc_rules.bnf
sys.path.insert(0, PROJECT_ROOT)            # 使 compiler_project/ 成为可导入模块
sys.path.insert(0, GEN_DIR)                 # 使 generator/ 作为包可导入

# ---------------------------------------------------------
# 3. 正确导入三大生成器（包结构）
# ---------------------------------------------------------
from generator.lex_builder import LexBuilder
from generator.yacc_builder import YaccBuilder
from generator.action_builder import ActionBuilder

# ---------------------------------------------------------
# 4. 配置文件路径（需为绝对路径）
# ---------------------------------------------------------
LEX_RULES = os.path.join(PROJECT_ROOT, "config", "lex_rules.lex")
YACC_RULES = os.path.join(PROJECT_ROOT, "config", "yacc_rules.bnf")

# 输出目录
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "generated_compiler")

# ---------------------------------------------------------
# 工具：确保输出目录存在
# ---------------------------------------------------------
def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

# ---------------------------------------------------------
# 5. 主流程
# ---------------------------------------------------------
def main():
    ensure_output_dir()

    # 1️⃣ 生成 lexer.py
    print("[A] 生成 lexer.py ...")
    lex_builder = LexBuilder(LEX_RULES)
    lexer_code = lex_builder.build()
    lexer_path = os.path.join(OUTPUT_DIR, "lexer.py")
    with open(lexer_path, "w", encoding="utf-8") as f:
        f.write(lexer_code)
    print(f"✔ lexer.py 已生成 → {lexer_path}")

    # 2️⃣ 生成 temp_parser.py（LL(1) 语法分析，无语义动作）
    print("[B] 生成 temp_parser.py ...")
    yacc_builder = YaccBuilder(YACC_RULES)
    temp_parser_path = os.path.join(OUTPUT_DIR, "temp_parser.py")
    yacc_builder.run(out_path=temp_parser_path)
    print(f"✔ temp_parser.py 已生成 → {temp_parser_path}")

    # 3️⃣ 注入语义动作 → parser.py
    print("[C] 注入语义动作，生成 parser.py ...")
    action_builder = ActionBuilder(parser_file=temp_parser_path)
    final_parser_code = action_builder.build()
    parser_path = os.path.join(OUTPUT_DIR, "parser.py")
    with open(parser_path, "w", encoding="utf-8") as f:
        f.write(final_parser_code)
    print(f"✔ parser.py 已生成 → {parser_path}")

    print("\n🎉 编译器全部生成完成！")

# ---------------------------------------------------------
# Entry
# ---------------------------------------------------------
if __name__ == "__main__":
    main()
