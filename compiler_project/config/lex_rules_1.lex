# ===================== SQL 风格词法规则 =====================

# 1. 忽略空白
WS          [ \t\r\n]+

# 2. SQL 风格注释 (以 -- 开头，直到行尾)
# 注意：RegexParser 中 . 匹配除换行外的所有字符
COMMENT     --.*

# 3. 关键字 (全部大写，优先级最高)
SET         SET
SELECT      SELECT
FROM        FROM
WHERE       WHERE
INSERT      INSERT
INTO        INTO
VALUES      VALUES
AND         AND
OR          OR
NULL        NULL

# 4. 复杂运算符 (必须放在单字符之前)
# Pascal/SQL 风格赋值
ASSIGN      :=
# SQL 不等于
NE          <>
# 比较运算
GE          >=
LE          <=

# 5. 单字符界符
SEMI        ;
COMMA       ,
LPAREN      [(]
RPAREN      [)]
EQ          =
GT          >
LT          <
STAR        [*]
PLUS        [+]

# 6. 字面量
# 十六进制 (例如 0xFF) - 测试混合字母数字
HEX         0x[0-9A-F]+

# 整数
NUMBER      [0-9]+

# SQL 字符串 (单引号包裹)
# 注意：这里简化处理，不包含转义
STRING      '[a-zA-Z0-9_ ]*'

# 7. 变量 (以 @ 开头，如 @myVar)
VARIABLE    @[a-zA-Z_][a-zA-Z0-9_]*

# 8. 普通标识符 (表名、列名)
IDENTIFIER  [a-zA-Z_][a-zA-Z0-9_]*