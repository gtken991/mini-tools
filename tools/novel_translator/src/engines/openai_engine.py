#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenAI翻译引擎
"""

import os
import time
from typing import List, Dict, Any
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import TranslationEngine
from ..config import OPENAI_API_KEY, LANGUAGE_MAP

class OpenAITranslationEngine(TranslationEngine):
    """OpenAI翻译引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key", OPENAI_API_KEY)
        if not self.api_key:
            raise ValueError("OpenAI API密钥未设置")
        
        # 初始化客户端
        self.client = OpenAI(api_key=self.api_key)
        
        # OpenAI配置
        openai_config = config.get("openai", {})
        self.model = openai_config.get("model", "gpt-3.5-turbo")
        self.temperature = openai_config.get("temperature", 0.3)
        self.context_size = openai_config.get("context_size", 3)
        self.system_prompt = openai_config.get("system_prompt", 
            "你是一个专业的小说翻译器，请将以下文本翻译成{target_language}，保持原文的风格、情感和文学性。请保留原文的段落结构。"
        )
        
        # 成本估算（美元/1K tokens）
        self.cost_map = {
            "gpt-3.5-turbo": {
                "input": 0.0005,
                "output": 0.0015
            },
            "gpt-4": {
                "input": 0.03,
                "output": 0.06
            },
            "gpt-4o": {
                "input": 0.01,
                "output": 0.03
            }
        }
        self.token_to_char_ratio = 0.75  # 每个token约等于0.75个中文字符或1.5个英文字符
        
    def get_name(self) -> str:
        return f"OpenAI ({self.model})"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def translate(self, text: str) -> str:
        """
        使用OpenAI API翻译文本
        
        Args:
            text: 待翻译文本
            
        Returns:
            翻译后的文本
        """
        if not text.strip():
            return ""
        
        # 替换系统提示中的目标语言
        target_lang = self._get_language_name(self.target_language)
        system_prompt = self.system_prompt.format(target_language=target_lang)
        
        # 调用API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=self.temperature
        )
        
        # 返回结果
        return response.choices[0].message.content.strip()
    
    def batch_translate(self, texts: List[str]) -> List[str]:
        """
        批量翻译文本
        
        Args:
            texts: 待翻译文本列表
            
        Returns:
            翻译后的文本列表
        """
        # OpenAI没有批量接口，所以我们顺序翻译
        results = []
        for text in texts:
            results.append(self.translate(text))
        return results
    
    def translate_with_context(self, text: str, context_before: List[str] = None, context_after: List[str] = None) -> str:
        """
        使用上下文进行翻译
        
        Args:
            text: 待翻译文本
            context_before: 前文上下文
            context_after: 后文上下文
            
        Returns:
            翻译后的文本
        """
        if not text.strip():
            return ""
        
        # 构建提示
        target_lang = self._get_language_name(self.target_language)
        system_prompt = self.system_prompt.format(target_language=target_lang)
        
        # 构建消息
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # 添加前文上下文
        if context_before and len(context_before) > 0:
            context_str = "\n\n".join(context_before)
            messages.append({
                "role": "user", 
                "content": f"以下是前文内容，仅供参考，不需要翻译：\n\n{context_str}"
            })
            messages.append({
                "role": "assistant",
                "content": "我明白了，这是前文的上下文。"
            })
        
        # 添加后文上下文
        if context_after and len(context_after) > 0:
            context_str = "\n\n".join(context_after)
            messages.append({
                "role": "user", 
                "content": f"以下是后文内容，仅供参考，不需要翻译：\n\n{context_str}"
            })
            messages.append({
                "role": "assistant",
                "content": "我明白了，这是后文的上下文。"
            })
        
        # 添加待翻译文本
        messages.append({
            "role": "user",
            "content": f"请翻译以下文本，保持原文的风格和语气：\n\n{text}"
        })
        
        # 调用API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature
        )
        
        # 返回结果
        return response.choices[0].message.content.strip()
    
    def estimate_cost(self, text: str) -> float:
        """
        估算翻译成本（美元）
        
        Args:
            text: 待翻译文本
            
        Returns:
            估算成本（美元）
        """
        if self.model not in self.cost_map:
            return 0.0
            
        # 估算token数量
        input_tokens = len(text) * self.token_to_char_ratio
        output_tokens = input_tokens * 1.2  # 假设输出比输入多20%
        
        # 计算成本
        input_cost = (input_tokens / 1000) * self.cost_map[self.model]["input"]
        output_cost = (output_tokens / 1000) * self.cost_map[self.model]["output"]
        
        return input_cost + output_cost
    
    def _get_language_name(self, language: str) -> str:
        """
        获取语言的完整名称
        
        Args:
            language: 语言代码
            
        Returns:
            语言的完整名称
        """
        if language in LANGUAGE_MAP and "openai" in LANGUAGE_MAP[language]:
            return LANGUAGE_MAP[language]["openai"]
        
        # 常见语言的名称映射
        language_names = {
            "zh": "Chinese",
            "en": "English",
            "ja": "Japanese",
            "ko": "Korean",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "ru": "Russian",
            "pt": "Portuguese",
            "it": "Italian"
        }
        
        return language_names.get(language, language) 