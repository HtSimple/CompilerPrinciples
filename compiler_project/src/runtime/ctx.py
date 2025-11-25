# src/runtime/ctx.py
# --------------------------------------------
# 中间代码生成上下文（Context）
# 提供临时变量生成、标签管理、TAC 生成和输出
# --------------------------------------------

from typing import List, Optional

class Context:
    """
    语义上下文，用于语法分析时生成三地址码（TAC）。
    """
    def __init__(self):
        self.temp_count = 0        # 临时变量计数
        self.label_count = 0       # 标签计数
        self.code: List[str] = []  # 三地址码列表

    # ---------------- 临时变量管理 ----------------
    def new_temp(self) -> str:
        """
        生成新的临时变量名
        t0, t1, t2 ...
        """
        name = f"t{self.temp_count}"
        self.temp_count += 1
        return name

    # ---------------- 标签管理 ----------------
    def new_label(self) -> str:
        """
        生成新的标签
        L0, L1, ...
        """
        label = f"L{self.label_count}"
        self.label_count += 1
        return label

    # ---------------- 代码生成 ----------------
    def emit(self, code_line: str):
        """
        添加一行三地址码
        """
        self.code.append(code_line)

    def emit_label(self, label: str):
        """
        添加标签
        """
        self.code.append(f"{label}:")

    def get_code(self) -> List[str]:
        """
        返回当前生成的三地址码列表
        """
        return self.code

    def write_code_to_file(self, filename: str):
        """
        输出三地址码到文件
        """
        with open(filename, "w") as f:
            for line in self.code:
                f.write(line + "\n")
