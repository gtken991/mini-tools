#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
翻译引擎包初始化
"""

from typing import Dict, Any, Type
from ..models import TranslationEngine
from .caiyun_engine import CaiyunTranslationEngine
from .openai_engine import OpenAITranslationEngine

# 注册所有引擎
ENGINE_REGISTRY = {
    "caiyun": CaiyunTranslationEngine,
    "openai": OpenAITranslationEngine,
}

def get_engine(name: str, config: Dict[str, Any]) -> TranslationEngine:
    """
    获取翻译引擎实例
    
    Args:
        name: 引擎名称
        config: 配置字典
        
    Returns:
        翻译引擎实例
    
    Raises:
        ValueError: 引擎不存在
    """
    if name not in ENGINE_REGISTRY:
        raise ValueError(f"不支持的翻译引擎: {name}")
    
    return ENGINE_REGISTRY[name](config)

def list_engines() -> Dict[str, Type[TranslationEngine]]:
    """
    列出所有支持的翻译引擎
    
    Returns:
        翻译引擎字典
    """
    return ENGINE_REGISTRY 