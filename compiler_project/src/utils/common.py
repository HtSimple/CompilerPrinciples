# src/utils/common.py

import os
import sys
from typing import Any, Optional, List

# 全局常量
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
TEST_DIR = os.path.join(PROJECT_ROOT, "test")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

# 错误码
ERROR_CODE_FILE_NOT_FOUND = 1
ERROR_CODE_INVALID_INPUT = 2
ERROR_CODE_COMPILER_ERROR = 3

class CompilerError(Exception):
    """编译器错误的基类"""
    def __init__(self, message: str, line: Optional[int] = None, column: Optional[int] = None):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(self.message)

    def __str__(self):
        if self.line is not None and self.column is not None:
            return f"[{self.line}:{self.column}] {self.message}"
        return self.message

def read_file(file_path: str) -> str:
    """
    读取文件内容
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件内容字符串
        
    Raises:
        CompilerError: 如果文件不存在或无法读取
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise CompilerError(f"文件不存在: {file_path}")
    except IOError as e:
        raise CompilerError(f"读取文件失败: {file_path}, 错误: {str(e)}")

def write_file(file_path: str, content: str) -> None:
    """
    写入文件内容
    
    Args:
        file_path: 文件路径
        content: 要写入的内容
        
    Raises:
        CompilerError: 如果无法写入文件
    """
    try:
        # 创建父目录（如果不存在）
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except IOError as e:
        raise CompilerError(f"写入文件失败: {file_path}, 错误: {str(e)}")

def print_error(message: str, line: Optional[int] = None, column: Optional[int] = None) -> None:
    """
    打印错误信息
    
    Args:
        message: 错误信息
        line: 行号（可选）
        column: 列号（可选）
    """
    if line is not None and column is not None:
        print(f"\033[91m错误 [{line}:{column}]: {message}\033[0m", file=sys.stderr)
    else:
        print(f"\033[91m错误: {message}\033[0m", file=sys.stderr)

def print_info(message: str) -> None:
    """
    打印信息消息
    
    Args:
        message: 信息内容
    """
    print(f"\033[94m信息: {message}\033[0m")

def print_success(message: str) -> None:
    """
    打印成功消息
    
    Args:
        message: 成功内容
    """
    print(f"\033[92m成功: {message}\033[0m")

def get_file_extension(file_path: str) -> str:
    """
    获取文件扩展名
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件扩展名（小写）
    """
    return os.path.splitext(file_path)[1].lower()

def normalize_path(file_path: str) -> str:
    """
    规范化文件路径
    
    Args:
        file_path: 文件路径
        
    Returns:
        规范化后的绝对路径
    """
    return os.path.abspath(os.path.normpath(file_path))

def is_valid_file(file_path: str, allowed_extensions: Optional[List[str]] = None) -> bool:
    """
    检查文件是否存在且合法
    
    Args:
        file_path: 文件路径
        allowed_extensions: 允许的文件扩展名列表（可选）
        
    Returns:
        如果文件合法则返回 True，否则返回 False
    """
    if not os.path.isfile(file_path):
        return False
    
    if allowed_extensions:
        ext = get_file_extension(file_path)
        if ext not in allowed_extensions:
            return False
    
    return True

def format_token_list(tokens: List[Any]) -> str:
    """
    格式化 Token 列表以便于显示
    
    Args:
        tokens: Token 列表
        
    Returns:
        格式化后的字符串
    """
    return "\n".join([str(token) for token in tokens])

def get_line_from_position(text: str, position: int) -> int:
    """
    根据字符位置获取行号
    
    Args:
        text: 文本内容
        position: 字符位置（从 0 开始）
        
    Returns:
        行号（从 1 开始）
    """
    if position < 0:
        return 1
    return text[:position].count("\n") + 1

def get_column_from_position(text: str, position: int) -> int:
    """
    根据字符位置获取列号
    
    Args:
        text: 文本内容
        position: 字符位置（从 0 开始）
        
    Returns:
        列号（从 1 开始）
    """
    if position < 0:
        return 1
    last_newline = text[:position].rfind("\n")
    if last_newline == -1:
        return position + 1
    return position - last_newline

def create_output_dir() -> None:
    """
    创建输出目录（如果不存在）
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)