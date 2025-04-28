#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小说翻译工具模型定义
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel
import time
from datetime import datetime
import json
import os

# 数据模型定义
class Paragraph(BaseModel):
    """段落模型"""
    id: int
    content: str
    translated: str = ""
    chapter: Optional[int] = None
    is_title: bool = False
    is_translated: bool = False
    translation_time: float = 0
    tokens: int = 0
    attempts: int = 0
    metadata: Dict[str, Any] = {}
    
    def __str__(self) -> str:
        return f"Paragraph({self.id}, {self.content[:20]}{'...' if len(self.content) > 20 else ''})"

class Chapter(BaseModel):
    """章节模型"""
    id: int
    title: str
    paragraphs: List[int] = []  # 段落ID列表
    
    def __str__(self) -> str:
        return f"Chapter({self.id}, {self.title})"

class Document(BaseModel):
    """文档模型"""
    id: str
    title: str
    source_language: str
    target_language: str
    paragraphs: Dict[int, Paragraph] = {}
    chapters: Dict[int, Chapter] = {}
    metadata: Dict[str, Any] = {}
    
    def add_paragraph(self, content: str, is_title: bool = False, chapter_id: Optional[int] = None) -> int:
        """添加段落"""
        para_id = len(self.paragraphs)
        self.paragraphs[para_id] = Paragraph(
            id=para_id,
            content=content,
            is_title=is_title,
            chapter=chapter_id
        )
        if chapter_id is not None and chapter_id in self.chapters:
            self.chapters[chapter_id].paragraphs.append(para_id)
        return para_id
    
    def add_chapter(self, title: str) -> int:
        """添加章节"""
        chapter_id = len(self.chapters)
        self.chapters[chapter_id] = Chapter(
            id=chapter_id,
            title=title
        )
        # 同时添加标题段落
        para_id = self.add_paragraph(title, is_title=True, chapter_id=chapter_id)
        return chapter_id
    
    def get_progress(self) -> float:
        """获取翻译进度"""
        if not self.paragraphs:
            return 0.0
        
        translated = sum(1 for p in self.paragraphs.values() if p.is_translated)
        return translated / len(self.paragraphs) * 100
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计数据"""
        total_paras = len(self.paragraphs)
        translated_paras = sum(1 for p in self.paragraphs.values() if p.is_translated)
        total_tokens = sum(p.tokens for p in self.paragraphs.values())
        total_time = sum(p.translation_time for p in self.paragraphs.values())
        
        return {
            "total_paragraphs": total_paras,
            "translated_paragraphs": translated_paras,
            "progress": self.get_progress(),
            "total_tokens": total_tokens,
            "total_time": total_time,
            "average_time_per_paragraph": total_time / translated_paras if translated_paras else 0,
            "timestamp": datetime.now().isoformat()
        }
    
    def save_progress(self, path: str) -> None:
        """保存进度"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_progress(cls, path: str) -> 'Document':
        """加载进度"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)

# 翻译引擎接口
class TranslationEngine(ABC):
    """翻译引擎基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.source_language = config.get("source_language", "zh")
        self.target_language = config.get("target_language", "en")
    
    @abstractmethod
    def translate(self, text: str) -> str:
        """
        翻译文本
        
        Args:
            text: 待翻译文本
            
        Returns:
            翻译后的文本
        """
        pass
    
    @abstractmethod
    def batch_translate(self, texts: List[str]) -> List[str]:
        """
        批量翻译文本
        
        Args:
            texts: 待翻译文本列表
            
        Returns:
            翻译后的文本列表
        """
        pass
    
    def translate_with_retry(self, text: str, max_retries: int = 3, delay: float = 1.0) -> str:
        """
        带重试的翻译
        
        Args:
            text: 待翻译文本
            max_retries: 最大重试次数
            delay: 重试延迟(秒)
            
        Returns:
            翻译后的文本
        """
        attempts = 0
        last_error = None
        
        while attempts < max_retries:
            try:
                return self.translate(text)
            except Exception as e:
                attempts += 1
                last_error = e
                if attempts < max_retries:
                    time.sleep(delay * attempts)  # 指数退避
        
        # 达到最大重试次数后仍然失败
        raise Exception(f"翻译失败，已重试{max_retries}次: {last_error}")
    
    @abstractmethod
    def get_name(self) -> str:
        """获取引擎名称"""
        pass
    
    @abstractmethod
    def estimate_cost(self, text: str) -> float:
        """估算翻译成本"""
        pass 