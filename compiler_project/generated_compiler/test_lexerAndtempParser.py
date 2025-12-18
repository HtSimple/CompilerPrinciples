import sys
import os
from dataclasses import dataclass

# --------------------------
# 数据类：语法结构摘要（供中间代码生成）
# --------------------------
@dataclass
class SyntaxStructure:
    type: str
    name: str
    scope: str
    line: int
    attrs: dict


# --------------------------
# 路径配置
# --------------------------
sys.path.append(os.path.dirname(__file__) + "/..")

try:
    from lexer import Lexer, Token
    from generated_compiler.temp_parser import parse
except ImportError as e:
    raise ImportError("请先运行 generator_main.py 生成目标编译器！") from e


# --------------------------
# 语法结构提取（简化 AST 摘要）
# --------------------------
def extract_syntax_structures(tokens):
    structures = []
    current_func = None
    line_num = 1
    i = 0

    while i < len(tokens):
        tok = tokens[i]

        # ---------- 函数定义 ----------
        if tok.type in ("INT", "VOID") and i + 2 < len(tokens):
            if tokens[i+1].type == "IDENTIFIER" and tokens[i+2].type == "LPAREN":
                func_name = tokens[i+1].value
                current_func = func_name
                structures.append(SyntaxStructure(
                    type="函数定义",
                    name=func_name,
                    scope="全局",
                    line=line_num,
                    attrs={"返回值类型": tok.value}
                ))
                i += 3
                continue

        # ---------- 变量声明 ----------
        if tok.type in ("INT", "VOID") and i + 2 < len(tokens):
            if tokens[i+1].type == "IDENTIFIER" and tokens[i+2].type == "SEMI":
                structures.append(SyntaxStructure(
                    type="变量声明",
                    name=tokens[i+1].value,
                    scope=f"函数{current_func}内" if current_func else "全局",
                    line=line_num,
                    attrs={"变量类型": tok.value}
                ))
                i += 3
                continue

        # ---------- 赋值语句 ----------
        if tok.type == "SET" and i + 2 < len(tokens):
            if tokens[i+1].type == "IDENTIFIER" and tokens[i+2].type == "ASSIGN":
                expr = []
                j = i + 3
                while j < len(tokens) and tokens[j].type != "SEMI":
                    expr.append(tokens[j].value)
                    j += 1
                structures.append(SyntaxStructure(
                    type="赋值语句",
                    name=tokens[i+1].value,
                    scope=f"函数{current_func}内" if current_func else "全局",
                    line=line_num,
                    attrs={"表达式": " ".join(expr)}
                ))
                i = j + 1
                continue

        # ---------- 控制流 ----------
        if tok.type in ("IF", "WHILE"):
            cond = []
            j = i + 2
            while j < len(tokens) and tokens[j].type != "RPAREN":
                cond.append(tokens[j].value)
                j += 1
            structures.append(SyntaxStructure(
                type="if条件语句" if tok.type == "IF" else "while循环语句",
                name="",
                scope=f"函数{current_func}内" if current_func else "全局",
                line=line_num,
                attrs={"条件表达式": " ".join(cond)}
            ))
            i = j + 1
            continue

        # ---------- return ----------
        if tok.type == "RETURN":
            ret = []
            j = i + 1
            while j < len(tokens) and tokens[j].type != "SEMI":
                ret.append(tokens[j].value)
                j += 1
            structures.append(SyntaxStructure(
                type="return语句",
                name="",
                scope=f"函数{current_func}内" if current_func else "全局",
                line=line_num,
                attrs={"返回值": " ".join(ret) if ret else "空"}
            ))
            i = j + 1
            continue

        i += 1

    return structures


# --------------------------
# AST 摘要
# --------------------------
def generate_ast_summary(structures):
    lines = ["Program"]
    for s in structures:
        lines.append(f"  └── {s.type} {s.name} {s.attrs}")
    return "\n".join(lines)


# --------------------------
# 主测试
# --------------------------
if __name__ == "__main__":

    test_cases = {
        "✅ 正确程序": """
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
""",

        "❌ 词法错误-非法字符": """
int main() {
    int a;
    set a = 3 @ 5;
    return a;
}
""",

        "❌ 语法错误-缺少分号": """
int main() {
    int a
    return a;
}
""",

        "❌ 语法错误-括号不匹配": """
int main( {
    return 0;
}
""",

        "❌ 语法错误-if 缺右括号": """
int main() {
    if (1 > 0 {
        return 1;
    }
}
"""
    }

    for name, code in test_cases.items():
        print("\n" + "=" * 70)
        print(f"测试用例：{name}")
        print("=" * 70)
        print(code)

        # --------------------------
        # 1. 词法分析
        # --------------------------
        try:
            print("\n[1] 词法分析")
            lexer = Lexer(code)
            tokens = lexer.tokenize()

            for i, t in enumerate(tokens):
                print(f"{i:02d} | {t.type:<10} | {t.value}")

        except Exception as e:
            print("❌ 词法分析错误捕获：")
            print(e)
            continue   # 词法失败，直接测下一个用例

        # --------------------------
        # 2. 语法分析
        # --------------------------
        try:
            print("\n[2] 语法分析（LL(1)）")
            token_types = [t.type for t in tokens] + ['$']
            success = parse(token_types, verbose=True)

            if not success:
                print("❌ 语法分析失败")
                continue

        except Exception as e:
            print("❌ 语法分析错误捕获：")
            print(e)
            continue

        # --------------------------
        # 3. 语法结构摘要（仅在成功时）
        # --------------------------
        print("\n[3] 语法结构摘要")
        structures = extract_syntax_structures(tokens)
        for s in structures:
            print(s)

        print("\nAST 摘要：")
        print(generate_ast_summary(structures))
