#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小说翻译工具配置文件
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 基础路径
BASE_DIR = Path(__file__).resolve().parent

# API密钥配置（从环境变量读取）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CAIYUN_API_KEY = os.getenv("CAIYUN_API_KEY", "")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
AZURE_API_KEY = os.getenv("AZURE_API_KEY", "")

# 默认设置
DEFAULT_CONFIG = {
    # 通用设置
    "default_engine": "caiyun",  # 默认翻译引擎
    "source_language": "zh",  # 源语言
    "target_language": "en",  # 目标语言
    "batch_size": 1000,  # 批次翻译的字符数
    "timeout": 30,  # 请求超时时间(秒)
    "retry_times": 3,  # 重试次数
    "output_format": "txt",  # 输出格式 (txt, epub, docx)
    "parallel_requests": 3,  # 并行请求数
    "save_interval": 1,  # 多少段落保存一次进度
    
    # OpenAI配置
    "openai": {
        "model": "gpt-3.5-turbo",  # 模型选择: gpt-3.5-turbo, gpt-4
        "temperature": 0.3,  # 温度参数，越低越稳定
        "context_size": 3,  # 上下文段落数量
        "system_prompt": "你是一个专业的小说翻译器，请将以下文本翻译成{target_language}，保持原文的风格、情感和文学性。请保留原文的段落结构。"
    },
    
    # 彩云小译配置
    "caiyun": {
        "url": "http://api.interpreter.caiyunai.com/v1/translator",
        "direction": "auto",  # 翻译方向，auto为自动检测
        "request_interval": 0.5,  # 请求间隔(秒)
    },
    
    # DeepL配置
    "deepl": {
        "free_api": False,  # 是否使用免费API
        "formality": "default",  # 语气: default, more, less
    },
    
    # 本地化设置
    "cache_dir": str(BASE_DIR / "cache"),  # 缓存目录
    "log_dir": str(BASE_DIR / "logs"),  # 日志目录
    "output_dir": str(BASE_DIR / "output"),  # 输出目录
    
    # 高级选项
    "preserve_format": True,  # 保留格式
    "bilingual_output": False,  # 双语对照输出
    "glossary_file": "",  # 术语表文件
    "budget_limit": 0,  # 预算限制(元)，0为不限制
    "debug_mode": False,  # 调试模式
}

# 支持的语言映射
LANGUAGE_MAP = {
    # 源语言代码到目标引擎的语言代码映射
    "zh": {
        "openai": "Chinese",
        "caiyun": "zh",
        "deepl": "ZH",
        "google": "zh-CN",
        "azure": "zh-Hans",
    },
    "en": {
        "openai": "English",
        "caiyun": "en",
        "deepl": "EN",
        "google": "en",
        "azure": "en",
    },
    "ja": {
        "openai": "Japanese",
        "caiyun": "ja",
        "deepl": "JA",
        "google": "ja",
        "azure": "ja",
    },
    # 更多语言可以在这里添加
}

# 支持的引擎
SUPPORTED_ENGINES = [
    "openai",
    "caiyun", 
    "deepl",
    "google",
    "azure",
    "local"
]

# 创建必要的目录
for dir_path in [DEFAULT_CONFIG["cache_dir"], DEFAULT_CONFIG["log_dir"], DEFAULT_CONFIG["output_dir"]]:
    Path(dir_path).mkdir(parents=True, exist_ok=True) 