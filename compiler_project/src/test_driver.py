# test_driver.py
import os
import sys

# -----------------------------
# 将项目根目录加入 sys.path
# -----------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

# -----------------------------
# 导入生成的编译器
# -----------------------------
try:
    from generated_compiler import lexer
    from generated_compiler import parser
except ImportError:
    raise ImportError("请先运行 generator_main.py 生成目标编译器！")

# -----------------------------
# 简单 Lexer + Parser 测试函数
# -----------------------------
def run_test(file_path):
    if not os.path.exists(file_path):
        print(f"测试文件不存在: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    # 1️⃣ 词法分析
    token_list = lexer.tokenize(code)  # 直接调用 tokenize 函数
    print("Token 列表:", token_list)

    # 2️⃣ 语法分析
    result = parser.parse(token_list)
    if result:
        print("语法分析通过 ✅")
    else:
        print("语法分析失败 ❌")

    # 3️⃣ 如果 parser.py 会生成 TAC，可以直接查看 tac_output.txt
    tac_file = os.path.join(PROJECT_ROOT, "generated_compiler", "tac_output.txt")
    if os.path.exists(tac_file):
        with open(tac_file, "r", encoding="utf-8") as f:
            tac = f.read()
        print("中间代码 / TAC:")
        print(tac)
    else:
        print("未生成 TAC 文件。")

# -----------------------------
# CLI 运行
# -----------------------------
if __name__ == "__main__":
    import argparse

    parser_cli = argparse.ArgumentParser(description="测试生成的编译器")
    parser_cli.add_argument("source_file", help="待测试的源代码文件")
    args = parser_cli.parse_args()

    run_test(args.source_file)
