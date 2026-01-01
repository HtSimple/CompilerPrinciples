# ===================== Mini-C 词法规则 =====================

# 1. 忽略空白
WS          [ \t\r\n]+

# 2. 注释 (C++ 风格 //)
COMMENT     //.*

# 3. 关键字 (关键字优先匹配)
INT         int
FLOAT       float
VOID        void
RETURN      return
IF          if
ELSE        else
WHILE       while

# 4. 复杂运算符 (必须放在单字符之前)
# 关系运算
EQ          ==
NEQ         !=
LE          <=
GE          >=

# 5. 单字符运算符 & 界符
# 赋值 (C 语言中 = 是赋值)
ASSIGN      =

# 比较
LT          <
GT          >

# 算术
PLUS        [+]
MINUS       -
STAR        [*]
DIV         /

# 界符
LPAREN      [(]
RPAREN      [)]
LBRACE      [{]
RBRACE      [}]
SEMI        ;
COMMA       ,

# 6. 字面量
# 浮点数 (必须在整数之前匹配)
FLOAT_LITERAL   [0-9]+\.[0-9]+

# 整数
INT_LITERAL     [0-9]+

# 7. 标识符
IDENTIFIER      [a-zA-Z_][a-zA-Z0-9_]*