# ctx.py
"""
TACContext: 中间代码生成上下文
用于存放临时变量、生成三地址码（TAC）
"""

import os

class TACContext:
    def __init__(self):
        # 存放中间代码，每条代码格式为 (op, arg1, arg2, result)
        # 保持 tuple 形式，方便后续格式化
        self.code = []

        # 临时变量计数
        self.temp_count = 0

        # 标签计数（用于 if/while 等控制流）
        self.label_count = 0

    # 生成新的临时变量
    def new_temp(self):
        t = f"t{self.temp_count}"
        self.temp_count += 1
        return t

    # 生成新的标签
    def new_label(self):
        l = f"L{self.label_count}"
        self.label_count += 1
        return l

    # 添加一条三地址码
    def emit(self, op, arg1=None, arg2=None, result=None):
        """
        op: 操作符或指令名
        arg1, arg2: 操作数
        result: 结果
        存入统一的四元组，方便后续统一输出。
        """
        self.code.append((op, arg1, arg2, result))

    # 返回内部的 instructions（以字符串形式便于直接写文件或打印）
    def get_instructions(self):
        """
        返回格式化后的指令列表（每项为字符串）。
        格式化规则尽量通用：
        - 如果 result 存在： "result = arg1 op arg2" （省略 None 部分）
        - 否则： "op arg1 arg2"（省略 None）
        """
        out = []
        for op, a1, a2, res in self.code:
            # case: binary-like with result
            if res is not None:
                parts = []
                parts.append(str(res))
                parts.append("=")
                # left operand
                if a1 is not None:
                    parts.append(str(a1))
                # operation token
                if op is not None:
                    parts.append(str(op))
                # right operand
                if a2 is not None:
                    parts.append(str(a2))
                out.append(" ".join(parts))
            else:
                # no result: emit op and operands
                parts = []
                if op is not None:
                    parts.append(str(op))
                if a1 is not None:
                    parts.append(str(a1))
                if a2 is not None:
                    parts.append(str(a2))
                out.append(" ".join(parts))
        return out

    # 打印生成的 TAC（可供调试）
    def dump(self):
        for line in self.get_instructions():
            print(line)

    # 保存到文件
    def save(self, filename):
        # 确保目录存在
        dirname = os.path.dirname(filename)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            for line in self.get_instructions():
                f.write(line + "\n")
