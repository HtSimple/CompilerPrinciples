# generator_main.py
"""
Compiler Generator 主入口
依次执行：
1. 词法分析器生成 (A)
2. 语法分析器生成 (B)
3. 注入语义动作，生成最终 parser (C)
"""

import os

# 假设三人的模块如下
from lex_builder import LexBuilder
from yacc_builder import YaccBuilder
from action_builder import ActionBuilder

# 配置文件路径
LEX_RULES = os.path.join("..", "config", "lex_rules.lex")
YACC_RULES = os.path.join("..", "config", "yacc_rules.bnf")

# 输出路径
OUTPUT_DIR = os.path.join("..", "generated_compiler")

def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def main():
    ensure_output_dir()

    # -----------------------------
    # 1️⃣ 生成 lexer.py
    # -----------------------------
    print("[A] 生成 lexer.py ...")
    lex_builder = LexBuilder(LEX_RULES)
    lexer_code = lex_builder.build()
    with open(os.path.join(OUTPUT_DIR, "lexer.py"), "w", encoding="utf-8") as f:
        f.write(lexer_code)
    print("lexer.py 生成完成。")

    # -----------------------------
    # 2️⃣ 生成 temp_parser.py (无语义动作)
    # -----------------------------
    print("[B] 生成 temp_parser.py ...")
    yacc_builder = YaccBuilder(YACC_RULES)
    parser_code = yacc_builder.build()
    with open(os.path.join(OUTPUT_DIR, "temp_parser.py"), "w", encoding="utf-8") as f:
        f.write(parser_code)
    print("temp_parser.py 生成完成。")

    # -----------------------------
    # 3️⃣ 注入语义动作，生成最终 parser.py
    # -----------------------------
    print("[C] 注入语义动作，生成 parser.py ...")
    action_builder = ActionBuilder(
        parser_file=os.path.join(OUTPUT_DIR, "temp_parser.py")
    )
    final_parser_code = action_builder.build()
    with open(os.path.join(OUTPUT_DIR, "parser.py"), "w", encoding="utf-8") as f:
        f.write(final_parser_code)
    print("最终 parser.py 生成完成。")

if __name__ == "__main__":
    main()
