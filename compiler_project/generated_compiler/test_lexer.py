# test_lexer.py
import sys
import os

# 添加上级目录到模块搜索路径（保证能导入 lexer 和 temp_parser）
sys.path.append(os.path.dirname(__file__) + "/..")

from lexer import tokenize
from generated_compiler.temp_parser import parse

# 修改后的测试代码，符合现有 LL(1) 文法
test_code = """
int foo(int x) {
    int y;
    set y = x * 5 + 3;  
    if (y > 10) {
        return y;
    }
    while (y < 20) {
        set y = y + 1;  
    }
    return 0;
}

void bar() {
    return;
}
"""

# 词法分析
tokens = tokenize(test_code)

print("=== Tokens ===")
for t in tokens:
    print(f"Token(type={t.type}, value={t.value})")

# 将 Token 对象转换为 LL(1) parser 可识别的类型字符串序列
token_types = [t.type for t in tokens]
token_types.append('$')  # 添加 LL(1) parser 结束符

print("\n=== Parsing Result ===")
# 调用 LL(1) parser
success = parse(token_types, verbose=True)

if success:
    print("Parsing succeeded!")
else:
    print("Parsing failed: Syntax error detected.")
