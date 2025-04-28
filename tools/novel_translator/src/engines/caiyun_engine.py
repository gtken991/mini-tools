#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
彩云小译翻译引擎
"""

import requests
import json
import time
from typing import List, Dict, Any
import os
from ..models import TranslationEngine
from ..config import CAIYUN_API_KEY, LANGUAGE_MAP

class CaiyunTranslationEngine(TranslationEngine):
    """彩云小译翻译引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key", CAIYUN_API_KEY)
        if not self.api_key:
            raise ValueError("彩云小译API密钥未设置")
        
        # 彩云小译配置
        self.url = config.get("caiyun", {}).get("url", "http://api.interpreter.caiyunai.com/v1/translator")
        self.direction = config.get("caiyun", {}).get("direction", "auto")
        self.request_interval = config.get("caiyun", {}).get("request_interval", 0.5)
        
        # 彩云小译每千字符的成本（人民币）
        self.cost_per_thousand_chars = 0.4 # 按商用价格估算
    
    def get_name(self) -> str:
        return "彩云小译"
    
    def translate(self, text: str) -> str:
        """
        使用彩云小译API翻译文本
        
        Args:
            text: 待翻译文本
            
        Returns:
            翻译后的文本
        """
        if not text.strip():
            return ""
        
        # 构建请求头
        headers = {
            "content-type": "application/json",
            "x-authorization": f"token {self.api_key}"
        }
        
        # 构建请求体
        payload = {
            "source": text,
            "trans_type": f"{self._get_language_code(self.source_language)}2{self._get_language_code(self.target_language)}",
            "request_id": "demo",
            "detect": True,
        }
        
        # 发送请求
        response = requests.post(self.url, headers=headers, data=json.dumps(payload))
        
        # 检查响应状态
        if response.status_code != 200:
            raise Exception(f"翻译请求失败，状态码：{response.status_code}，响应：{response.text}")
        
        # 解析响应
        result = response.json()
        if "target" not in result:
            raise Exception(f"翻译响应格式错误：{result}")
        
        # 添加请求间隔以避免频率限制
        time.sleep(self.request_interval)
        
        return result["target"]
    
    def batch_translate(self, texts: List[str]) -> List[str]:
        """
        批量翻译文本
        
        Args:
            texts: 待翻译文本列表
            
        Returns:
            翻译后的文本列表
        """
        # 彩云小译没有批量接口，所以我们顺序翻译
        results = []
        for text in texts:
            results.append(self.translate(text))
        return results
    
    def estimate_cost(self, text: str) -> float:
        """
        估算翻译成本（人民币）
        
        Args:
            text: 待翻译文本
            
        Returns:
            估算成本（元）
        """
        char_count = len(text)
        return (char_count / 1000) * self.cost_per_thousand_chars
    
    def _get_language_code(self, language: str) -> str:
        """
        获取彩云小译的语言代码
        
        Args:
            language: 语言代码
            
        Returns:
            彩云小译的语言代码
        """
        if language in LANGUAGE_MAP and "caiyun" in LANGUAGE_MAP[language]:
            return LANGUAGE_MAP[language]["caiyun"]
        return language  # 回退到原始代码 