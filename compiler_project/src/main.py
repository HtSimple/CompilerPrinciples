# File: compiler_project/src/main.py
import sys
import os

# ==========================================================
# 1. 设置工程根目录，使所有模块可被正确 import
# ==========================================================
# 当前文件位置：compiler_project/src/main.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

# 将根目录加入 sys.path（generator/、src/、config/ 都位于此目录下）
sys.path.insert(0, PROJECT_ROOT)

# ==========================================================
# 2. 导入生成器主入口（generator_main.py）
# ==========================================================
from generator.generator_main import main as generate_compiler


# ==========================================================
# 3. 运行生成的编译器（lexer.py + parser.py）
# ==========================================================
def run_test_program(test_file):
    """
    使用生成的 lexer.py + parser.py 运行测试程序
    """

    GENERATED_DIR = os.path.join(PROJECT_ROOT, "generated_compiler")

    # 将 generated_compiler 加入 sys.path
    sys.path.insert(0, GENERATED_DIR)

    # 导入 lexer 和 parser
    import lexer
    import parser

    # 读取测试源代码
    with open(test_file, "r", encoding="utf-8") as f:
        code = f.read()

    # 词法分析 → 返回 token 对象列表
    tokens = lexer.tokenize(code)

    # 语法分析（针对 LL(1) 或 LR 你自己定义 parse 接口）
    try:
        ast = parser.parse(tokens)
        print("\n==========================")
        print("语法分析成功！输出 AST：")
        print("==========================")
        print(ast)
    except Exception as e:
        print("\n==========================")
        print("语法分析失败：")
        print("==========================")
        print(e)
        return


# ==========================================================
# 4. main 主流程：生成编译器 + 测试源程序
# ==========================================================
def main():
    print("==================================================")
    print(" Step 1: 生成目标编译器（Lexer / Parser）")
    print("==================================================")

    generate_compiler()

    print("\n==================================================")
    print(" Step 2: 运行测试源程序（test/example.src）")
    print("==================================================")

    test_src = os.path.join(PROJECT_ROOT, "test", "example.src")

    if os.path.exists(test_src):
        run_test_program(test_src)
    else:
        print(f"测试文件不存在: {test_src}")


if __name__ == "__main__":
    main()
