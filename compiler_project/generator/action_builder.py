import os
import inspect

from src.runtime.ctx import TACContext
from src.runtime.token import Node

TAC_OUTPUT_FILE = os.path.join("generated_compiler", "tac_output.txt")
# 在这个模块里保留一个 TACGEN 仅作为占位（注意：action 函数源码会被注入到 parser.py，
# 注入处会重新定义 TACGEN = TACContext()，注入后的 program() 将使用注入处的 TACGEN）
TACGEN = TACContext()

# ----------------- 动作函数 -----------------
def program(children):
    node = Node("program", children)
    # 输出 TAC：使用当前作用域的 TACGEN（注入到 parser.py 时，parser 将有自己的 TACGEN）
    # 直接调用 save，save 会创建目录并写入文件
    TACGEN.save(TAC_OUTPUT_FILE)
    return node

def function(children):
    node = Node("function", children)
    if children:
        # children 的结构取决于 parser，尽量使用 str() 兼容 token / node
        func_name = str(children[1]) if len(children) > 1 else "anonymous"
        TACGEN.emit("FUNC_BEGIN", func_name)
    return node

def var_decl_code(children):
    node = Node("var_decl", children)
    if children:
        var_name = str(children[1]) if len(children) > 1 else str(children[0])
        TACGEN.emit("VAR_DECL", var_name)
    return node

def assign_code(children):
    node = Node("assign", children)
    # 典型 children: [IDENTIFIER, expr_node_or_token]
    if len(children) >= 2:
        left = str(children[0])
        right = str(children[1])
        # 目前保持与现有 emit 调用兼容：emit(op, arg1, arg2, result)
        # 如果你后续希望用 "result = arg1 op arg2"，可以把 result 传入
        TACGEN.emit("ASSIGN", left, right)
    return node

def if_code(children):
    node = Node("if", children)
    TACGEN.emit("IF", str(children))
    return node

def while_code(children):
    node = Node("while", children)
    TACGEN.emit("WHILE", str(children))
    return node

def return_code(children):
    node = Node("return", children)
    if children:
        TACGEN.emit("RETURN", str(children[0]))
    return node

def expr_code(children):
    node = Node("expr", children)
    TACGEN.emit("EXPR", str(children))
    return node

def block_code(children):
    node = Node("block", children)
    TACGEN.emit("BLOCK", str(children))
    return node

def add(children):
    node = Node("add", children)
    if len(children) == 2:
        TACGEN.emit("ADD", str(children[0]), str(children[1]))
    return node

def sub(children):
    node = Node("sub", children)
    if len(children) == 2:
        TACGEN.emit("SUB", str(children[0]), str(children[1]))
    return node

def mul(children):
    node = Node("mul", children)
    if len(children) == 2:
        TACGEN.emit("MUL", str(children[0]), str(children[1]))
    return node

def div(children):
    node = Node("div", children)
    if len(children) == 2:
        TACGEN.emit("DIV", str(children[0]), str(children[1]))
    return node

ACTIONS = {
    "program": program,
    "function": function,
    "var_decl_code": var_decl_code,
    "assign_code": assign_code,
    "if_code": if_code,
    "while_code": while_code,
    "return_code": return_code,
    "expr_code": expr_code,
    "block_code": block_code,
    "add": add,
    "sub": sub,
    "mul": mul,
    "div": div,
}

# ----------------- ActionBuilder -----------------
class ActionBuilder:
    def __init__(self, parser_file):
        self.parser_file = parser_file

    def build(self):
        if not os.path.exists(self.parser_file):
            raise FileNotFoundError(f"{self.parser_file} 不存在")

        with open(self.parser_file, "r", encoding="utf-8") as f:
            parser_code = f.read()

        injected_code = parser_code + "\n\n# ===== 注入动作与 TAC =====\n"
        injected_code += "from src.runtime.ctx import TACContext\n"
        injected_code += "from src.runtime.token import Node\n"
        # 在注入的 parser 中创建 TACGEN（parser 运行时使用此实例）
        injected_code += "TACGEN = TACContext()\n\n"

        funcs_written = set()
        for func in ACTIONS.values():
            if func not in funcs_written:
                injected_code += inspect.getsource(func) + "\n\n"
                funcs_written.add(func)

        injected_code += "ACTIONS = {\n"
        for key, func in ACTIONS.items():
            injected_code += f"    '{key}': {func.__name__},\n"
        injected_code += "}\n\n"

        # 替换 parse() 中占位调用为真实动作调用（注：这是一个简单的驱动版）
        injected_code += '''
def parse_with_actions(token_list, verbose=True):
    from generated_compiler import temp_parser as tp
    # 使用原 parse() 构建的栈结构（简单驱动）
    stack = ['$']
    stack.append(tp.start_symbol)
    stack_nodes = []
    ip = 0
    while stack:
        top = stack.pop()
        lookahead = token_list[ip]
        if top == '$' or top not in tp.nonterminals:
            if top == lookahead:
                stack_nodes.append(lookahead)
                ip += 1
                if top == '$':
                    return True
                continue
            else:
                return False
        else:
            key = (top, lookahead)
            entry = tp.parse_table.get(key)
            if entry is None:
                return False
            left, right, action = entry
            for sym in reversed(right):
                stack.append(sym)
            if action:
                # pop children (终结符/非终结符都有对应的 stack_nodes 项)
                children = [stack_nodes.pop() for _ in right][::-1]
                node = ACTIONS[action](children)
                stack_nodes.append(node)
    return True
'''

        injected_code += f"\nEXPORT_TAC = TACGEN\n"
        return injected_code
