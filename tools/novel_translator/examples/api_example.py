#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小说翻译工具API使用示例
演示如何通过编程方式使用翻译工具
"""

import os
import sys
import json
from pathlib import Path

# 将项目根目录添加到路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# 导入翻译工具
from tools.novel_translator.src import NovelTranslator
from tools.novel_translator.src.utils import process_novel_text, read_text_file

def main():
    """主函数"""
    # 加载配置
    config_path = Path(current_dir).parent / "config" / "default_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 自定义配置
    config.update({
        "source_language": "zh",        # 源语言
        "target_language": "en",        # 目标语言
        "default_engine": "caiyun",     # 翻译引擎
        "output_format": "txt",         # 输出格式
        "bilingual_output": True,       # 是否双语输出
        "glossary_file": str(Path(current_dir) / "sample_glossary.txt"), # 术语表文件
        "output_dir": str(Path(current_dir).parent / "output")  # 输出目录
    })
    
    # 创建翻译器实例
    translator = NovelTranslator(config)
    
    # 方法1: 直接翻译文件
    input_file = Path(current_dir) / "sample_text.txt"
    output_file = translator.translate_file(
        file_path=str(input_file),
        output_format="txt",
        title="API示例翻译"
    )
    print(f"文件翻译完成，输出文件: {output_file}")
    
    # 方法2: 翻译文本内容
    sample_text = """
    这是一个示例文本。
    你可以直接翻译文本内容而不需要文件。
    这对于集成到其他应用程序中非常有用。
    """
    
    # 处理文本为Document对象
    document = process_novel_text(sample_text)
    document.source_language = "zh"
    document.target_language = "en"
    document.title = "内容翻译示例"
    
    # 翻译文档
    translated_doc = translator.translate_document(document)
    
    # 输出翻译结果
    print("\n翻译结果:")
    for para_id, para in sorted(translated_doc.paragraphs.items()):
        if para.is_translated:
            print(f"原文: {para.content}")
            print(f"译文: {para.translated}")
            print("---")

if __name__ == "__main__":
    main() 