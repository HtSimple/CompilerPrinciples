# ------------------------------------------
# lex_rules.lex
# ------------------------------------------
# 定义 token 类型与正则
# ------------------------------------------

# 关键字
IF      if
ELSE    else
WHILE   while
FOR     for
RETURN  return
INT     int
VOID    void

# 标识符
IDENTIFIER  [a-zA-Z_][a-zA-Z0-9_]*

# 数字字面量
NUMBER      [0-9]+

# 字符串字面量
STRING      "([^"\\]|\\.)*"

# 运算符
PLUS        \+
MINUS       \-
MULT        \*
DIV         /
ASSIGN      =
EQ          ==
NE          !=
LT          <
GT          >
LE          <=
GE          >=

# 界符
LPAREN      \(
RPAREN      \)
LBRACE      \{
RBRACE      \}
SEMI        ;
COMMA       ,

# 空白符忽略
WHITESPACE  [ \t\n]+    -> skip

# 文件结束
EOF         <<EOF>>
