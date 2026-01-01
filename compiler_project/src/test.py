from generated_compiler.lexer import Lexer
from generated_compiler.parser import parse, EXPORT_TAC

with open("simple.pl0", "r", encoding="utf-8") as f:
    source = f.read()

lexer = Lexer(source)
tokens = lexer.tokenize()
ast = parse(tokens, verbose=True)

print("\n=== AST ===")
print(ast)

print("\n=== TAC ===")
for tac in EXPORT_TAC.code:
    print(tac)
