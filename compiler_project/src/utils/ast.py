from typing import List, Optional, Union
from .token import Token  # 引入Token类用于类型注解

class ASTNode:
    """
    抽象语法树（AST）节点类
    
    属性:
        node_type (str): 节点类型（如 'Program', 'BinaryExpr', 'Identifier'）
        children (List[ASTNode]): 子节点列表
        value (Optional[Union[str, int, float]]): 节点的值（可选，如变量名、常量值）
        token (Optional[Token]): 关联的Token（可选，用于错误定位）
    """
    
    def __init__(self, 
                 node_type: str, 
                 children: Optional[List['ASTNode']] = None, 
                 value: Optional[Union[str, int, float]] = None, 
                 token: Optional[Token] = None):
        self.node_type = node_type
        self.children = children if children is not None else []
        self.value = value
        self.token = token  # 保留关联的Token，便于后续错误提示和调试

    def add_child(self, child: 'ASTNode'):
        """
        向当前节点添加子节点
        
        Args:
            child (ASTNode): 要添加的子节点
        """
        self.children.append(child)

    def get_children(self) -> List['ASTNode']:
        """
        获取当前节点的所有子节点
        
        Returns:
            List[ASTNode]: 子节点列表（返回副本，避免外部直接修改）
        """
        return self.children.copy()

    def __repr__(self):
        """
        返回节点的详细字符串表示（便于调试）
        
        Returns:
            str: 包含节点类型、值、子节点数量和关联Token的字符串
        """
        token_info = f"token={self.token}" if self.token else "no token"
        return (f"ASTNode(type='{self.node_type}', value={self.value!r}, "
                f"children={len(self.children)}, {token_info})")

    def __str__(self, indent: int = 0) -> str:
        """
        返回节点的树形字符串表示（便于可视化AST结构）
        
        Args:
            indent (int): 缩进级别（用于控制树形显示的层级）
            
        Returns:
            str: 树形结构的字符串
        """
        indent_str = "  " * indent
        value_str = f": {self.value}" if self.value is not None else ""
        result = f"{indent_str}{self.node_type}{value_str}\n"
        
        for child in self.children:
            result += child.__str__(indent + 1)
        
        return result
    
    def print_tree(self, indent=0):
        """递归打印 AST 树状结构"""
        result = "  " * indent + f"{self.node_type}"
        if self.value is not None:
            result += f": {self.value}"
        if self.token:
            result += f" (Line: {self.token.line})"
        result += "\n"
        
        for child in self.children:
            result += child.print_tree(indent + 1)
        
        return result
