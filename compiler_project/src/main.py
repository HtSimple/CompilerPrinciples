# src/main.py
# --------------------------------------------
# 主程序：调用生成的编译器对单个源程序生成 TAC
# --------------------------------------------

import sys
from generated_compiler import lexer, parser

def compile_source_file(source_file: str, tac_output_file: str = "generated_compiler/tac_output.txt"):
    # 读取源代码
    with open(source_file, "r") as f:
        source_code = f.read()

    # 词法分析
    tokens = lexer.tokenize(source_code)  # 假设 lexer.py 提供 tokenize() 函数
    print(f"[INFO] {len(tokens)} tokens generated.")

    # 语法分析 + SDT 生成中间代码
    tac_list = parser.parse(tokens)       # 假设 parser.py 提供 parse()，返回 TAC 列表
    print(f"[INFO] {len(tac_list)} TAC instructions generated.")

    # 输出 TAC
    with open(tac_output_file, "w") as f:
        for instr in tac_list:
            f.write(instr + "\n")
    print(f"[INFO] TAC written to {tac_output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <source_file>")
        sys.exit(1)

    source_file = sys.argv[1]
    compile_source_file(source_file)
