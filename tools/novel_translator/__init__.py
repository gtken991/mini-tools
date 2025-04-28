#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小说翻译工具包
"""

import os
import sys

# 确保可以导入src包
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 设置版本信息
__version__ = "0.2.0"
__author__ = "AI小说翻译工具团队"

# 尝试直接导入模块
try:
    from src.translator import NovelTranslator
    from src.models import Document, Paragraph, Chapter, TranslationEngine
    from src.engines import get_engine, list_engines
    from src.output_formats import get_formatter, list_formats
    from src.utils import process_novel_text, read_text_file, write_text_file, detect_file_encoding, load_glossary
    
    # 尝试导入GUI组件
    try:
        from src.gui import NovelTranslatorGUI
        has_gui = True
    except ImportError:
        has_gui = False
        
    # 定义公开的API
    __all__ = [
        "NovelTranslator",
        "Document",
        "Paragraph",
        "Chapter",
        "TranslationEngine",
        "get_engine",
        "list_engines",
        "get_formatter",
        "list_formats",
        "process_novel_text",
        "read_text_file",
        "write_text_file",
        "detect_file_encoding",
        "load_glossary",
        "__version__",
        "__author__",
    ]
    
    # 如果GUI组件可用，添加到__all__
    if has_gui:
        __all__.append("NovelTranslatorGUI")
        
except ImportError as e:
    # 出错时提供有用的错误消息
    print(f"导入小说翻译工具组件时出错: {e}")
    print("请确保您已安装所有必要的依赖，可通过 pip install -r requirements.txt 安装")
    
    # 设置空的__all__，避免导入错误
    __all__ = [] 