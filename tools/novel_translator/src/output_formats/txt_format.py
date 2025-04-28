#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文本格式输出
"""

import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..models import Document, Paragraph, Chapter
from ..utils import ensure_dir, write_text_file

def format_as_txt(document: Document, options: Dict[str, Any], output_path: str) -> str:
    """
    将文档导出为文本格式
    
    Args:
        document: 文档对象
        options: 格式选项
        output_path: 输出路径
        
    Returns:
        输出文件路径
    """
    # 解析选项
    bilingual = options.get("bilingual_output", False)
    include_titles = options.get("include_titles", True)
    encoding = options.get("encoding", "utf-8")
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    ensure_dir(output_dir)
    
    # 构建输出内容
    lines = []
    
    # 添加标题
    if document.title:
        lines.append(document.title)
        lines.append("=" * len(document.title))
        lines.append("")
    
    # 按顺序处理每个段落
    sorted_paras = sorted(document.paragraphs.values(), key=lambda p: p.id)
    
    # 当前章节
    current_chapter = None
    
    for para in sorted_paras:
        # 检查是否为章节标题
        if para.is_title and include_titles:
            chapter_id = para.chapter
            if chapter_id is not None and chapter_id in document.chapters:
                chapter = document.chapters[chapter_id]
                current_chapter = chapter
                
                lines.append("")
                lines.append(para.content)
                lines.append("-" * len(para.content))
                
                if bilingual and para.is_translated:
                    lines.append(para.translated)
                    lines.append("-" * len(para.translated))
                
                lines.append("")
        # 普通段落
        elif not para.is_title:
            # 添加原文
            lines.append(para.content)
            
            # 如果是双语模式，添加译文
            if bilingual and para.is_translated:
                lines.append("")
                lines.append(para.translated)
            
            lines.append("")
    
    # 写入文件
    content = "\n".join(lines)
    write_text_file(output_path, content, encoding)
    
    # 如果是双语模式，再生成两个单语言的版本
    if bilingual:
        # 源语言版本
        source_path = f"{os.path.splitext(output_path)[0]}_source.txt"
        format_single_language_txt(document, False, source_path, encoding)
        
        # 目标语言版本
        target_path = f"{os.path.splitext(output_path)[0]}_target.txt"
        format_single_language_txt(document, True, target_path, encoding)
    
    return output_path

def format_single_language_txt(document: Document, target_language: bool, output_path: str, encoding: str = "utf-8") -> str:
    """
    将文档导出为单语言文本格式
    
    Args:
        document: 文档对象
        target_language: 是否为目标语言
        output_path: 输出路径
        encoding: 文件编码
        
    Returns:
        输出文件路径
    """
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    ensure_dir(output_dir)
    
    # 构建输出内容
    lines = []
    
    # 添加标题
    if document.title:
        lines.append(document.title)
        lines.append("=" * len(document.title))
        lines.append("")
    
    # 按顺序处理每个段落
    sorted_paras = sorted(document.paragraphs.values(), key=lambda p: p.id)
    
    # 当前章节
    current_chapter = None
    
    for para in sorted_paras:
        # 检查是否为章节标题
        if para.is_title:
            chapter_id = para.chapter
            if chapter_id is not None and chapter_id in document.chapters:
                chapter = document.chapters[chapter_id]
                current_chapter = chapter
                
                lines.append("")
                if target_language and para.is_translated:
                    lines.append(para.translated)
                    lines.append("-" * len(para.translated))
                else:
                    lines.append(para.content)
                    lines.append("-" * len(para.content))
                
                lines.append("")
        # 普通段落
        elif not para.is_title:
            # 根据语言选择
            if target_language and para.is_translated:
                lines.append(para.translated)
            else:
                lines.append(para.content)
            
            lines.append("")
    
    # 写入文件
    content = "\n".join(lines)
    write_text_file(output_path, content, encoding)
    
    return output_path 