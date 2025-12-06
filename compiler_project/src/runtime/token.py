# token.py
"""
Node: 语法树/抽象语法树节点
每个节点对应语法规则或语义动作的结果
"""

class Node:
    def __init__(self, nodetype, children=None, value=None):
        """
        nodetype: 节点类型（如 <expr>, <assign_stmt>, #add 等）
        children: 子节点列表
        value: 叶子节点的值（如标识符名、数字、字符串）
        """
        self.nodetype = nodetype
        self.children = children if children is not None else []
        self.value = value

    def __repr__(self):
        if self.value is not None:
            return f"Node({self.nodetype}, value={self.value})"
        elif self.children:
            return f"Node({self.nodetype}, children={self.children})"
        else:
            return f"Node({self.nodetype})"

    # 递归打印树结构
    def pretty(self, indent=0):
        pad = "  " * indent
        if self.value is not None:
            print(f"{pad}{self.nodetype}: {self.value}")
        else:
            print(f"{pad}{self.nodetype}")
            for child in self.children:
                if isinstance(child, Node):
                    child.pretty(indent + 1)
                else:
                    print(f"{'  '*(indent+1)}{child}")

    # 遍历所有节点，支持语义动作执行或中间代码生成
    def traverse(self, func):
        """
        func: 一个回调函数，参数为 Node，自行处理 TAC 或 AST
        """
        func(self)
        for child in self.children:
            if isinstance(child, Node):
                child.traverse(func)
