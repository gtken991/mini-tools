#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
输出格式处理包
"""

from typing import Dict, Any, Callable
from ..models import Document

# 输出格式处理函数类型
OutputFormatterFn = Callable[[Document, Dict[str, Any], str], str]

# 导入所有格式处理模块
from .txt_format import format_as_txt
from .epub_format import format_as_epub
from .docx_format import format_as_docx

# 注册所有格式处理函数
FORMAT_REGISTRY = {
    "txt": format_as_txt,
    "epub": format_as_epub,
    "docx": format_as_docx,
}

def get_formatter(format_name: str) -> OutputFormatterFn:
    """
    获取格式处理函数
    
    Args:
        format_name: 格式名称
        
    Returns:
        格式处理函数
        
    Raises:
        ValueError: 不支持的格式
    """
    if format_name not in FORMAT_REGISTRY:
        raise ValueError(f"不支持的输出格式: {format_name}")
    
    return FORMAT_REGISTRY[format_name]

def list_formats() -> Dict[str, OutputFormatterFn]:
    """
    列出所有支持的输出格式
    
    Returns:
        格式处理函数字典
    """
    return FORMAT_REGISTRY