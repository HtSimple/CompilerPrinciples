# 关键字
IF          if
ELSE        else
WHILE       while
RETURN      return
INT         int
VOID        void
SET         set

# 标识符
IDENTIFIER  [a-zA-Z_][a-zA-Z0-9_]*

# 数字字面量
NUMBER      [0-9]+

# 字符串字面量
STRING      "([^"\\]|\\.)*"

# 注释
COMMENT     //.*
COMMENT     /\*[\s\S]*?\*/

# 运算符（多字符放前）
LE          <=
GE          >=
EQ          ==
NE          !=
LT          <
GT          >
ASSIGN      =
PLUS        \+
MINUS       \-
MULT        \*
DIV         /

# 界符
LPAREN      \(
RPAREN      \)
LBRACE      \{
RBRACE      \}
SEMI        ;
COMMA       ,

# 空白符
WS          [ \t\r\n]+
