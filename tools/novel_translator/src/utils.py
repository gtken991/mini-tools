#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小说翻译工具的工具函数
"""

import os
import re
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import unicodedata
import chardet
import nltk
from nltk.tokenize import sent_tokenize
import logging
from datetime import datetime

from .models import Document, Paragraph, Chapter

# 尝试下载NLTK数据
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("novel_translator")

def detect_encoding(file_path: str) -> str:
    """
    检测文件编码
    
    Args:
        file_path: 文件路径
        
    Returns:
        检测到的编码
    """
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def read_text_file(file_path: str) -> str:
    """
    读取文本文件，自动检测编码
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件内容
    """
    encoding = detect_encoding(file_path)
    with open(file_path, 'r', encoding=encoding) as f:
        return f.read()

def write_text_file(file_path: str, content: str, encoding: str = 'utf-8') -> None:
    """
    写入文本文件
    
    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 编码
    """
    with open(file_path, 'w', encoding=encoding) as f:
        f.write(content)

def ensure_dir(path: str) -> str:
    """
    确保目录存在
    
    Args:
        path: 目录路径
        
    Returns:
        路径
    """
    os.makedirs(path, exist_ok=True)
    return path

def normalize_text(text: str) -> str:
    """
    规范化文本（去除多余空白，规范化Unicode等）
    
    Args:
        text: 文本
        
    Returns:
        规范化后的文本
    """
    # 规范化Unicode
    text = unicodedata.normalize('NFKC', text)
    
    # 去除多余空白
    text = re.sub(r'\s+', ' ', text)
    
    # 规范化引号
    text = re.sub(r'[""]', '"', text)
    text = re.sub(r'['']', "'", text)
    
    return text.strip()

def split_paragraphs(text: str) -> List[str]:
    """
    将文本分割为段落
    
    Args:
        text: 文本
        
    Returns:
        段落列表
    """
    # 按连续的空行分割
    paragraphs = re.split(r'\n\s*\n', text)
    
    # 过滤空段落
    return [p.strip() for p in paragraphs if p.strip()]

def is_chapter_title(text: str) -> bool:
    """
    判断文本是否为章节标题
    
    Args:
        text: 文本
        
    Returns:
        是否为章节标题
    """
    # 常见的章节标题模式
    patterns = [
        r'^第\s*[0-9零一二三四五六七八九十百千万]+\s*[章节回集卷]',  # 中文章节（第一章、第1章）
        r'^Chapter\s*[0-9]+',  # 英文章节
        r'^CHAPTER\s*[0-9]+',
        r'^[0-9]+\.',  # 数字标题 (1., 2.)
        r'^[一二三四五六七八九十]+、',  # 中文数字标题 (一、二、)
    ]
    
    # 判断是否匹配任一模式
    return any(re.match(pattern, text) for pattern in patterns)

def extract_chapter_number(title: str) -> Optional[int]:
    """
    从章节标题中提取章节号
    
    Args:
        title: 章节标题
        
    Returns:
        章节号，无法提取则返回None
    """
    # 中文数字映射
    cn_num = {
        '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
        '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
        '十': 10, '百': 100, '千': 1000, '万': 10000
    }
    
    # 尝试匹配中文章节
    match = re.search(r'第\s*([0-9零一二三四五六七八九十百千万]+)\s*[章节回集卷]', title)
    if match:
        num_str = match.group(1)
        # 判断是否为阿拉伯数字
        if num_str.isdigit():
            return int(num_str)
        else:
            # 简单的中文数字转换，仅支持简单数字
            if len(num_str) == 1 and num_str in cn_num:
                return cn_num[num_str]
            # 对于复杂中文数字，这里仅做概略实现
            # 完整实现请参考专门的中文数字转换库
            total = 0
            temp = 0
            for c in num_str:
                if c in cn_num:
                    if cn_num[c] < 10:
                        temp = temp * 10 + cn_num[c]
                    else:
                        if temp == 0:
                            temp = 1
                        temp *= cn_num[c]
                        total += temp
                        temp = 0
            total += temp
            return total if total > 0 else None
    
    # 尝试匹配英文章节
    match = re.search(r'Chapter\s*([0-9]+)', title, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # 尝试匹配数字标题
    match = re.search(r'^([0-9]+)\.', title)
    if match:
        return int(match.group(1))
    
    return None

def process_novel_text(text: str) -> Document:
    """
    处理小说文本，解析为文档结构
    
    Args:
        text: 小说文本
        
    Returns:
        文档对象
    """
    # 规范化文本
    text = normalize_text(text)
    
    # 分割段落
    paragraphs = split_paragraphs(text)
    
    # 创建文档
    document = Document(
        id=f"novel_{int(time.time())}",
        title="未命名小说",
        source_language="zh",
        target_language="en"
    )
    
    # 检测标题
    if paragraphs and len(paragraphs[0]) < 100:
        document.title = paragraphs[0]
        paragraphs = paragraphs[1:]
    
    # 当前章节ID
    current_chapter_id = None
    
    # 处理所有段落
    for paragraph in paragraphs:
        # 检查是否为章节标题
        if is_chapter_title(paragraph):
            # 添加新章节
            current_chapter_id = document.add_chapter(paragraph)
        else:
            # 添加正文段落
            document.add_paragraph(paragraph, chapter_id=current_chapter_id)
    
    return document

def estimate_translation_cost(document: Document, engine: str, char_cost: float = None) -> Dict[str, Any]:
    """
    估算翻译成本
    
    Args:
        document: 文档对象
        engine: 引擎名称
        char_cost: 每千字符的成本（人民币）
        
    Returns:
        成本信息
    """
    # 计算总字符数
    total_chars = sum(len(p.content) for p in document.paragraphs.values())
    
    if engine == "caiyun":
        # 彩云小译计算（以元为单位）
        if char_cost is None:
            char_cost = 0.4  # 商用价格约0.4元/千字符
        cost = (total_chars / 1000) * char_cost
        currency = "CNY"
    elif engine == "openai":
        # OpenAI计算（以美元为单位）
        # 约0.0005美元/1K输入tokens，0.0015美元/1K输出tokens
        token_ratio = 0.75  # 每个中文字符约0.75个token
        input_tokens = total_chars * token_ratio
        output_tokens = input_tokens * 1.2  # 假设输出比输入多20%
        input_cost = (input_tokens / 1000) * 0.0005  # gpt-3.5-turbo输入成本
        output_cost = (output_tokens / 1000) * 0.0015  # gpt-3.5-turbo输出成本
        cost = input_cost + output_cost
        currency = "USD"
    else:
        # 默认按字符数计算
        if char_cost is None:
            char_cost = 0.5  # 默认每千字符0.5元
        cost = (total_chars / 1000) * char_cost
        currency = "CNY"
    
    return {
        "total_chars": total_chars,
        "cost": round(cost, 2),
        "currency": currency,
        "engine": engine
    }

def generate_translation_report(document: Document, cost_info: Dict[str, Any], duration: float) -> str:
    """
    生成翻译报告
    
    Args:
        document: 文档对象
        cost_info: 成本信息
        duration: 翻译耗时（秒）
        
    Returns:
        报告文本
    """
    stats = document.get_statistics()
    
    report = [
        "# 翻译报告",
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 文档信息",
        f"标题: {document.title}",
        f"源语言: {document.source_language}",
        f"目标语言: {document.target_language}",
        f"段落数: {stats['total_paragraphs']}",
        f"章节数: {len(document.chapters)}",
        f"总字符数: {cost_info['total_chars']}",
        "",
        "## 翻译信息",
        f"翻译引擎: {cost_info['engine']}",
        f"翻译进度: {stats['progress']:.2f}%",
        f"已翻译段落: {stats['translated_paragraphs']}/{stats['total_paragraphs']}",
        f"翻译耗时: {duration:.2f}秒",
        f"平均速度: {cost_info['total_chars']/duration:.2f}字符/秒",
        "",
        "## 成本信息",
        f"总成本: {cost_info['cost']} {cost_info['currency']}",
        f"单位成本: {cost_info['cost']*1000/cost_info['total_chars']:.4f} {cost_info['currency']}/千字符",
    ]
    
    return "\n".join(report)

def load_glossary(file_path: str) -> Dict[str, str]:
    """
    加载术语表
    
    Args:
        file_path: 术语表文件路径
        
    Returns:
        术语表字典
    """
    if not os.path.exists(file_path):
        return {}
    
    result = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('=', 1)
                if len(parts) == 2:
                    source, target = parts
                    result[source.strip()] = target.strip()
    except Exception as e:
        logger.error(f"加载术语表出错: {e}")
        
    return result 