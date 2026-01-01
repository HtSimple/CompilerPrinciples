# 编译器生成器程序设计文档

## 1. 项目概述

### 1.1 项目背景
本项目是编译原理期末项目，旨在实现一个编译器的编译器（Compiler Generator），能够根据词法规则和语法规则自动生成对应的词法分析器和语法分析器。项目采用Python语言实现，实现了经典的编译器构造算法，包括NFA/DFA构造、LL(1)语法分析、语法制导翻译等技术。

### 1.2 项目目标
- 实现词法分析器的自动生成，基于正则表达式规则
- 实现语法分析器的自动生成，采用LL(1)分析方法
- 支持中间代码生成，使用语法制导翻译方法
- 实现三地址码（TAC）的生成和输出

### 1.3 团队成员
- 夏弘泰
- 陈帆
- 张昊天

## 2. 系统设计

### 2.1 总体架构
项目采用模块化设计，主要分为以下几个部分：
- **词法分析器生成器**（LexBuilder）：负责将词法规则转换为DFA并生成词法分析器
- **语法分析器生成器**（YaccBuilder）：负责计算FIRST/FOLLOW集并生成LL(1)分析表
- **运行时组件**：提供Token、AST节点、TAC上下文等基础数据结构
- **中间代码翻译**：使用语法制导翻译，将源代码翻译为TAC

### 2.2 目录结构
```
compiler_project/
├── generator/                    # 编译器生成器模块
│   ├── lex_builder.py           # NFA/DFA 构造器
│   ├── yacc_builder.py          # LL(1) 表构造器
│   ├── action_builder.py        # 语义动作构造器
│   └── generator_main.py        # 生成器主入口
├── generated_compiler/          # 生成的目标编译器
│   ├── lexer.py                 # 生成的词法分析器
│   ├── parser.py                # 生成的语法分析器
│   └── .gitkeep                 # 保持目录结构
├── config/                      # 配置文件目录
│   ├── lex_rules_1.lex          # PL/0 词法规则
│   ├── lex_rules_2.lex          # C 语言词法规则
│   ├── lex_rules_3.lex          # SQL 词法规则
│   ├── yacc_rules_1.bnf         # PL/0 语法规则
│   ├── yacc_rules_2.bnf         # C 语言语法规则
│   └── yacc_rules_3.bnf         # SQL 语法规则
├── intermediate code/           # 中间代码翻译模块
│   ├── lexer.py                 # 中间代码词法分析器
│   ├── parser.py                # 中间代码语法分析器
│   ├── test.py                  # 中间代码测试
│   ├── simple1.pl0             # PL/0 测试程序1
│   ├── simple2.pl0             # PL/0 测试程序2
│   ├── simple3.pl0             # PL/0 测试程序3
│   └── generated_compiler/     # 中间代码生成器输出
├── src/                         # 源代码和运行时组件
│   ├── main.py                  # 项目主入口
│   ├── test.py                  # 主测试文件
│   ├── test_driver.py           # 测试驱动程序
│   ├── simple.pl0               # 简单PL/0程序
│   └── runtime/                 # 运行时支持库
│       ├── token.py             # Token 数据结构
│       └── ctx.py               # TAC 生成上下文
└── test/                        # 测试文件目录
    ├── test.py                  # 测试主程序
    ├── PL0_test_code_right.txt  # PL/0 正确测试用例
    ├── PL0_test_code_false.txt  # PL/0 错误测试用例
    ├── C_test_code_right.txt    # C 语言正确测试用例
    ├── C_test_code_false.txt    # C 语言错误测试用例
    ├── sql_test_code_right.txt  # SQL 正确测试用例
    ├── sql_test_code_false.txt  # SQL 错误测试用例
    └── .gitkeep                 # 保持目录结构
```

### 2.3 核心算法设计

#### 2.3.1 词法分析算法
采用Thompson构造法构建NFA，然后通过子集构造法转换为DFA，最后使用等价状态法进行DFA最小化。

**主要步骤：**
1. 正则表达式解析：支持基本正则操作符（*、+、?、|、()、[]）和转义字符
2. NFA构造：基于Thompson构造法将正则表达式转换为NFA
3. DFA转换：通过ε-闭包和子集构造法将NFA转换为DFA
4. DFA最小化：使用等价状态法减少状态数
5. 代码生成：将DFA转换为可执行的词法分析器代码

#### 2.3.2 语法分析算法
采用LL(1)语法分析方法，通过计算FIRST和FOLLOW集合构建分析表。

**主要步骤：**
1. BNF文法解析：解析BNF格式的语法规则
2. FIRST集计算：递归计算每个符号的FIRST集
3. FOLLOW集计算：基于FIRST集计算每个非终结符的FOLLOW集
4. 预测分析表构建：根据FIRST和FOLLOW集构建LL(1)分析表
5. 预测分析器生成：生成基于分析表的预测分析器

#### 2.3.3 中间代码生成算法
采用语法制导翻译方法，在语法分析过程中生成三地址码。

**主要步骤：**
1. 语义动作定义：为每个语法规则定义相应的语义动作
2. 临时变量生成：动态生成临时变量用于表达式计算
3. 标签生成：生成控制流语句所需的标签
4. 三地址码生成：按照标准格式生成三地址码

## 3. 系统实现

### 3.1 词法分析器生成器实现

#### 3.1.1 NFA状态表示
```python
class NFAState:
    def __init__(self):
        self.id = NFAState._id_counter
        NFAState._id_counter += 1
        self.transitions = {}       # char -> set(states)
        self.epsilon = set()        # ε-transitions
        self.accepting = None       # (priority, name)
```

#### 3.1.2 正则表达式解析器
实现了支持多种正则操作符的解析器，包括：
- 基本操作符：连接、选择（|）、闭包（*）、正闭包（+）、可选（?）
- 分组：()
- 字符类：[]
- 转义字符：\n, \t, \r等

#### 3.1.3 NFA构造算法
根据正则表达式的结构递归构造NFA：
- 基本字符：创建包含两个状态的简单NFA
- 连接：将前一个NFA的终态与后一个NFA的初态连接
- 选择：创建新的初态和终态，通过ε-转换连接两个NFA
- 闭包：通过ε-转换实现自循环

#### 3.1.4 DFA转换与最小化
- ε-闭包计算：计算状态集合的ε-闭包
- 子集构造：将NFA状态集合转换为DFA状态
- 最小化：使用等价类划分算法减少DFA状态数

### 3.2 语法分析器生成器实现

#### 3.2.1 文法表示
使用BNF格式表示上下文无关文法，支持ε产生式。

#### 3.2.2 FIRST集计算算法
```python
def compute_first(self):
    for t in self.terminals: self.first[t] = {t}
    for nt in self.nonterminals: self.first[nt] = set()
    
    changed = True
    while changed:
        changed = False
        for lhs, rhs, _ in self.productions:
            # 计算右部序列的 FIRST
            seq_first = set()
            all_nullable = True
            
            if not rhs: # 空产生式
                seq_first = {EPSILON}
            else:
                for sym in rhs:
                    sym_first = self.first[sym]
                    seq_first.update(sym_first - {EPSILON})
                    if EPSILON not in sym_first:
                        all_nullable = False
                        break
                if all_nullable:
                    seq_first.add(EPSILON)

            # 更新 LHS 的 FIRST
            if not seq_first.issubset(self.first[lhs]):
                self.first[lhs].update(seq_first)
                changed = True
```

#### 3.2.3 FOLLOW集计算算法
基于FIRST集递归计算FOLLOW集，处理右部符号对左部符号FOLLOW集的影响。

#### 3.2.4 预测分析表构建
根据FIRST和FOLLOW集构建LL(1)分析表：
- 对于产生式A → α，将FIRST(α)中的所有终结符加入M[A, a]
- 如果ε ∈ FIRST(α)，则将FOLLOW(A)中的所有符号加入M[A, a]

### 3.3 语义动作与中间代码生成

#### 3.3.1 语义动作定义
为每个语法规则定义相应的语义动作函数，如：
- 表达式求值：生成算术运算的三地址码
- 赋值语句：生成赋值操作的三地址码
- 控制流语句：生成条件跳转和标签

#### 3.3.2 TAC上下文管理
```python
class TACContext:
    def __init__(self):
        self.code = []              # 存放中间代码
        self.temp_count = 0         # 临时变量计数
        self.label_count = 0        # 标签计数

    def new_temp(self):
        t = f"t{self.temp_count}"
        self.temp_count += 1
        return t

    def new_label(self):
        l = f"L{self.label_count}"
        self.label_count += 1
        return l

    def emit(self, op, arg1=None, arg2=None, result=None):
        self.code.append((op, arg1, arg2, result))
```

## 4. 系统测试

### 4.1 测试用例设计
设计了多种类型的测试用例，包括：
- 基本词法分析测试：验证各种Token的识别
- 语法分析测试：验证各种语句的语法正确性
- 中间代码生成测试：验证生成的三地址码正确性
- 错误处理测试：验证错误输入的处理

### 4.2 测试结果
- 词法分析器：能够正确识别不同语言风格的关键词、标识符、字面量等
- 语法分析器：能够正确解析各种语言的语句
- 中间代码生成：能够生成符合预期的三地址码
- 错误处理：能够检测并报告语法错误

## 5. AI助手使用说明

在项目开发过程中，使用AI助手完成了以下任务：
- 代码结构设计和架构规划
- 算法实现和调试
- 代码优化和重构
- 文档编写和格式化
- 问题诊断和解决方案制定

AI助手帮助提高了开发效率，特别是在复杂算法实现和错误调试方面提供了重要支持。

## 6. 总结与展望

本项目成功实现了编译器生成器，包括词法分析器生成、语法分析器生成和中间代码生成三个核心功能。系统具有良好的模块化设计，算法实现正确，测试结果符合预期。

未来可以考虑的改进方向：
- 支持更多类型的语法分析算法（如LR、LALR）
- 增强错误恢复和错误报告机制
- 支持更复杂的语义分析功能
- 提供图形化界面和可视化工具