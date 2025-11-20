import argparse
from src.parser import parse
from src.utils.token import Token
from src.utils.common import CompilerError

def main():
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description="语法分析器检验工具 (手动输入 Token)")
    parser.add_argument("--test-case", type=int, default=1, help="选择预定义的测试用例 (1-4)")
    
    args = parser.parse_args()

    # --- 在这里定义你的测试用例 ---
    # 每个测试用例都是一个 Token 列表
    test_cases = {
        1: [
            # 测试用例 1: 合法赋值语句 x = 10 + 20 * 3;
            Token('ID', 'x', 1, 1),
            Token('ASSIGN', '=', 1, 3),
            Token('INT', '10', 1, 5),
            Token('PLUS', '+', 1, 8),
            Token('INT', '20', 1, 10),
            Token('MUL', '*', 1, 13),
            Token('INT', '3', 1, 15),
            Token('SEMICOLON', ';', 1, 16)
        ],
        2: [
            # 测试用例 2: 非法语句 - 缺少分号
            Token('ID', 'x', 1, 1),
            Token('ASSIGN', '=', 1, 3),
            Token('INT', '10', 1, 5)
            # 故意缺少 SEMICOLON
        ],
        3: [
            # 测试用例 3: 非法语句 - 括号不匹配
            Token('ID', 'x', 1, 1),
            Token('ASSIGN', '=', 1, 3),
            Token('LPAREN', '(', 1, 5),
            Token('INT', '10', 1, 6),
            Token('PLUS', '+', 1, 9),
            Token('INT', '20', 1, 11)
            # 故意缺少 RPAREN 和 SEMICOLON
        ],
        4: [
            # 测试用例 4: 合法的嵌套表达式
            Token('ID', 'y', 1, 1),
            Token('ASSIGN', '=', 1, 3),
            Token('LPAREN', '(', 1, 5),
            Token('ID', 'a', 1, 6),
            Token('PLUS', '+', 1, 8),
            Token('ID', 'b', 1, 10),
            Token('RPAREN', ')', 1, 11),
            Token('MUL', '*', 1, 13),
            Token('LPAREN', '(', 1, 15),
            Token('ID', 'c', 1, 16),
            Token('MINUS', '-', 1, 18),
            Token('ID', 'd', 1, 20),
            Token('RPAREN', ')', 1, 21),
            Token('SEMICOLON', ';', 1, 22)
        ]
    }

    # 选择测试用例
    if args.test_case not in test_cases:
        print(f"错误：测试用例 {args.test_case} 不存在。请选择 1-4。")
        return

    selected_tokens = test_cases[args.test_case]
    
    print(f"=== 正在运行测试用例 {args.test_case} ===")
    print("输入的 Token 列表:")
    for token in selected_tokens:
        print(token)
    print("-" * 30)

    try:
        # 调用语法分析器
        ast_root = parse(selected_tokens)
        
        # 如果没有抛出异常，说明语法分析成功
        print("✅ 语法分析成功！输入的 Token 流符合语法规则。")
        
        # （可选）如果你的 AST 有打印功能，可以在这里调用
        # print("\n生成的抽象语法树 (AST):")
        # print(ast_root.print_tree())

    except CompilerError as e:
        # 捕获并打印语法错误
        print(f"\n❌ 语法分析失败: {e}")
    except Exception as e:
        # 捕获其他未知错误
        print(f"\n❌ 发生未知错误: {e}")

if __name__ == "__main__":
    main()