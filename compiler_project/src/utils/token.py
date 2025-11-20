class Token:
    """
    词法分析器生成的token（记号）类
    
    属性:
        type_ (str): token类型（如 'ID', 'PLUS', 'INT'）
        value (str): token的具体值（如变量名 'x'、运算符 '+'、数字 '123'）
        line (int): token在源代码中的行号（从1开始）
        column (int): token在源代码中的列号（从1开始）
    """
    
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __eq__(self, other):
        """
        判断两个Token是否相等（忽略位置信息，仅比较类型和值）
        
        Args:
            other (Token): 要比较的另一个Token对象
            
        Returns:
            bool: 若类型和值都相同则返回True，否则返回False
        """
        if not isinstance(other, Token):
            return False
        return self.type == other.type and self.value == other.value

    def __repr__(self):
        """
        返回Token的字符串表示（便于调试）
        
        Returns:
            str: 包含Token类型、值、行号和列号的字符串
        """
        return (f"Token(type='{self.type}', value='{self.value}', "
                f"line={self.line}, column={self.column})")

    def __str__(self):
        """
        返回Token的简洁字符串表示（便于打印）
        
        Returns:
            str: 包含类型和值的字符串
        """
        return f"<{self.type}: {self.value}>"