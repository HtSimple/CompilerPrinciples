import sys
import os
from dataclasses import dataclass

# --------------------------
# 数据类：存储语法结构关键信息（供中间代码生成参考）
# --------------------------
@dataclass
class SyntaxStructure:
    """语法结构摘要，面向中间代码生成人员"""
    type: str          # 结构类型（函数定义/变量声明/赋值语句等）
    name: str          # 名称（函数名/变量名）
    scope: str         # 作用域（全局/函数内）
    line: int          # 所在行号
    attrs: dict        # 附加属性（如参数列表、返回值类型、表达式等）

# --------------------------
# 路径配置与模块导入
# --------------------------
# 添加上级目录到模块搜索路径（保证能导入 lexer 和 temp_parser）
sys.path.append(os.path.dirname(__file__) + "/..")

try:
    from lexer import tokenize
    from generated_compiler.temp_parser import parse
except ImportError as e:
    raise ImportError("请先运行 generator_main.py 生成目标编译器！") from e

# --------------------------
# 核心辅助函数：提取语法结构信息（模拟AST摘要，实际可从parser返回值获取）
# --------------------------
def extract_syntax_structures(tokens):
    """
    从Token列表提取关键语法结构信息
    （实际项目中可替换为parser返回的AST解析结果）
    """
    structures = []
    current_func = None  # 当前处理的函数
    line_num = 1         # 行号追踪
    token_idx = 0        # Token索引

    while token_idx < len(tokens):
        token = tokens[token_idx]
        # 追踪行号（基于换行符）
        if token.value == "\n":
            line_num += 1
            token_idx += 1
            continue

        # 1. 识别函数定义（int/void + 标识符 + (）
        if token.type in ["INT", "VOID"] and token_idx + 2 < len(tokens):
            next1 = tokens[token_idx + 1]
            next2 = tokens[token_idx + 2]
            if next1.type == "IDENTIFIER" and next2.type == "LPAREN":
                func_type = token.value
                func_name = next1.value
                current_func = func_name
                # 提取参数列表（简化版）
                params = []
                param_idx = token_idx + 3
                while param_idx < len(tokens) and tokens[param_idx].type != "RPAREN":
                    if tokens[param_idx].type in ["INT", "VOID"] and param_idx + 1 < len(tokens):
                        param_type = tokens[param_idx].value
                        param_name = tokens[param_idx + 1].value
                        params.append({"name": param_name, "type": param_type})
                        param_idx += 2
                    param_idx += 1
                # 添加函数定义结构
                structures.append(SyntaxStructure(
                    type="函数定义",
                    name=func_name,
                    scope="全局",
                    line=line_num,
                    attrs={"返回值类型": func_type, "参数列表": params}
                ))
                token_idx += 3
                continue

        # 2. 识别变量声明（int/void + 标识符 + ;）
        if token.type in ["INT", "VOID"] and token_idx + 2 < len(tokens):
            next1 = tokens[token_idx + 1]
            next2 = tokens[token_idx + 2]
            if next1.type == "IDENTIFIER" and next2.type == "SEMI":
                var_name = next1.value
                var_type = token.value
                structures.append(SyntaxStructure(
                    type="变量声明",
                    name=var_name,
                    scope=f"函数{current_func}内" if current_func else "全局",
                    line=line_num,
                    attrs={"变量类型": var_type}
                ))
                token_idx += 3
                continue

        # 3. 识别赋值语句（set + 标识符 + =）
        if token.type == "SET" and token_idx + 2 < len(tokens):
            next1 = tokens[token_idx + 1]
            next2 = tokens[token_idx + 2]
            if next1.type == "IDENTIFIER" and next2.type == "ASSIGN":
                target_var = next1.value
                # 提取表达式（简化版）
                expr_tokens = []
                expr_idx = token_idx + 3
                while expr_idx < len(tokens) and tokens[expr_idx].type != "SEMI":
                    expr_tokens.append(f"{tokens[expr_idx].value}")
                    expr_idx += 1
                expr = " ".join(expr_tokens)
                structures.append(SyntaxStructure(
                    type="赋值语句",
                    name=target_var,
                    scope=f"函数{current_func}内" if current_func else "全局",
                    line=line_num,
                    attrs={"表达式": expr}
                ))
                token_idx += 3
                continue

        # 4. 识别控制流语句（if/while）
        if token.type in ["IF", "WHILE"] and token_idx + 1 < len(tokens) and tokens[token_idx + 1].type == "LPAREN":
            stmt_type = "if条件语句" if token.type == "IF" else "while循环语句"
            # 提取条件表达式
            cond_tokens = []
            cond_idx = token_idx + 2
            while cond_idx < len(tokens) and tokens[cond_idx].type != "RPAREN":
                cond_tokens.append(tokens[cond_idx].value)
                cond_idx += 1
            cond = " ".join(cond_tokens)
            structures.append(SyntaxStructure(
                type=stmt_type,
                name="",
                scope=f"函数{current_func}内" if current_func else "全局",
                line=line_num,
                attrs={"条件表达式": cond}
            ))
            token_idx += 2
            continue

        # 5. 识别return语句
        if token.type == "RETURN":
            # 提取返回值
            return_val = ""
            ret_idx = token_idx + 1
            while ret_idx < len(tokens) and tokens[ret_idx].type != "SEMI":
                return_val += tokens[ret_idx].value + " "
                ret_idx += 1
            return_val = return_val.strip()
            structures.append(SyntaxStructure(
                type="return语句",
                name="",
                scope=f"函数{current_func}内" if current_func else "全局",
                line=line_num,
                attrs={"返回值": return_val if return_val else "空"}
            ))
            token_idx += 1
            continue

        token_idx += 1

    return structures

# --------------------------
# 生成AST摘要（面向中间代码生成）
# --------------------------
def generate_ast_summary(structures):
    """生成简化的AST摘要字符串"""
    ast_lines = ["Program"]
    func_structures = [s for s in structures if s.type == "函数定义"]
    for func in func_structures:
        ast_lines.append(f"└── FunctionDef(name={func.name}, return_type={func.attrs['返回值类型']})")
        ast_lines.append(f"    ├── ParamList: {func.attrs['参数列表']}")
        ast_lines.append(f"    └── StmtList")
        # 提取该函数内的语句
        func_stmts = [s for s in structures if s.scope == f"函数{func.name}内" and s.type != "函数定义"]
        for stmt in func_stmts:
            if stmt.type == "变量声明":
                ast_lines.append(f"        ├── VarDecl(name={stmt.name}, type={stmt.attrs['变量类型']})")
            elif stmt.type == "赋值语句":
                ast_lines.append(f"        ├── AssignStmt(target={stmt.name}, expr={stmt.attrs['表达式']})")
            elif stmt.type == "if条件语句":
                ast_lines.append(f"        ├── IfStmt(cond={stmt.attrs['条件表达式']})")
            elif stmt.type == "while循环语句":
                ast_lines.append(f"        ├── WhileStmt(cond={stmt.attrs['条件表达式']})")
            elif stmt.type == "return语句":
                ast_lines.append(f"        ├── ReturnStmt({stmt.attrs['返回值']})")
    return "\n".join(ast_lines)

# --------------------------
# 主测试逻辑
# --------------------------
if __name__ == "__main__":
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

    # --------------------------
    # 1. 词法分析
    # --------------------------
    print("=" * 50)
    print("1. 词法分析结果（带核心上下文）")
    print("=" * 50)
    tokens = tokenize(test_code)
    for idx, t in enumerate(tokens):
        # 过滤纯空白符（保留有意义Token）
        if t.type not in ["WHITESPACE", "NEWLINE"] or t.value.strip() != "":
            print(f"Token[{idx}] | type={t.type:<12} | value={t.value:<8}")

    # --------------------------
    # 2. 语法分析
    # --------------------------
    print("\n" + "=" * 50)
    print("2. LL(1) 语法分析过程")
    print("=" * 50)
    # 将 Token 对象转换为 LL(1) parser 可识别的类型字符串序列
    token_types = [t.type for t in tokens if t.type not in ["WHITESPACE", "NEWLINE"]]
    token_types.append('$')  # 添加 LL(1) parser 结束符

    # 调用 LL(1) parser
    success = parse(token_types, verbose=True)

    # --------------------------
    # 3. 语法分析结果总结（面向中间代码生成）
    # --------------------------
    print("\n" + "=" * 50)
    print("3. 语法编译器运行总结（供中间代码生成参考）")
    print("=" * 50)
    if success:
        print("✅ 语法分析状态：通过（无语法错误）")
        
        # 提取语法结构信息
        syntax_structures = extract_syntax_structures(tokens)
        
        # 3.1 核心语法结构清单
        print("\n📋 识别到的核心语法结构：")
        for idx, struct in enumerate(syntax_structures, 1):
            print(f"   {idx}. {struct.type}")
            print(f"      - 名称/作用域：{struct.name or '无'} | {struct.scope}")
            # print(f"      - 行号：{struct.line}")
            print(f"      - 关键属性：{struct.attrs}")
        
        # 3.2 AST摘要（简化版）
        print("\n🌳 AST结构摘要：")
        ast_summary = generate_ast_summary(syntax_structures)
        print(f"   {ast_summary}")
        
        # 3.3 中间代码生成建议
        print("\n💡 中间代码生成建议：")
        print("   - 函数foo：局部变量y分配栈空间，表达式x*5+3需按优先级生成（t1=x*5; t2=t1+3; y=t2）")
        print("   - 函数bar：无参数无返回值，return语句生成空返回指令")
        print("   - 控制流：if/while条件需生成跳转指令，循环体需处理终止条件")
        
    else:
        print("❌ 语法分析状态：失败（检测到语法错误）")
        print("\n❓ 错误排查建议（供中间代码生成参考）：")
        print("   - 请先修复语法错误（如缺少分号、括号不匹配、关键字拼写错误）")
        print("   - 错误位置可结合上方『语法分析过程』的STACK TOP/LOOKAHEAD不匹配处定位")
        print("   - 修复后重新运行测试，确认语法通过后再进行中间代码生成")

    print("\n" + "=" * 50)
    print("4. 测试完成")
    print("=" * 50)