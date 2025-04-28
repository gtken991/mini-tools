#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小说翻译工具包
"""

from .translator import NovelTranslator
from .models import Document, Paragraph, Chapter, TranslationEngine
from .engines import get_engine, list_engines
from .output_formats import get_formatter, list_formats
from .utils import process_novel_text

# 添加GUI相关导出
try:
    from .gui import NovelTranslatorGUI
except ImportError:
    # GUI依赖可能未安装（如tkinter），此时不导出GUI组件
    pass

__version__ = "0.1.0"
__author__ = "小说翻译工具开发团队"

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
]

# 如果GUI组件可用，添加到__all__
try:
    if "NovelTranslatorGUI" in globals():
        __all__.append("NovelTranslatorGUI")
except:
    pass 