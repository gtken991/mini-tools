#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小说翻译工具主模块
"""

import os
import time
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import concurrent.futures
from tqdm import tqdm
import argparse
import signal
import sys
from pathlib import Path

from .models import Document, Paragraph, Chapter, TranslationEngine
from .engines import get_engine, list_engines
from .output_formats import get_formatter, list_formats
from .utils import (
    read_text_file, write_text_file, process_novel_text, 
    estimate_translation_cost, generate_translation_report,
    load_glossary
)
from .config import DEFAULT_CONFIG

class NovelTranslator:
    """小说翻译器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化翻译器
        
        Args:
            config: 配置字典，不传递则使用默认配置
        """
        self.config = config or DEFAULT_CONFIG.copy()
        self.logger = logging.getLogger("novel_translator")
        
        # 初始化翻译引擎
        engine_name = self.config.get("default_engine", "caiyun")
        self.engine = get_engine(engine_name, self.config)
        
        # 加载术语表
        self.glossary = {}
        glossary_file = self.config.get("glossary_file", "")
        if glossary_file:
            self.glossary = load_glossary(glossary_file)
        
        # 创建输出目录
        output_dir = self.config.get("output_dir", "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # 进度保存路径
        self.progress_dir = Path(self.config.get("cache_dir", "cache"))
        self.progress_dir.mkdir(exist_ok=True, parents=True)
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)
        
        self.current_document = None
        
        # 进度回调函数
        self.progress_callback = None
    
    def set_progress_callback(self, callback):
        """
        设置进度回调函数
        
        Args:
            callback: 回调函数，接收三个参数：当前段落索引，总段落数，当前段落文本
                      返回True继续翻译，返回False暂停翻译
        """
        self.progress_callback = callback
    
    def translate_file(self, file_path: str, output_format: str = None, **kwargs) -> str:
        """
        翻译文件
        
        Args:
            file_path: 文件路径
            output_format: 输出格式，不传则使用配置中的默认格式
            **kwargs: 其他参数，将覆盖配置
            
        Returns:
            输出文件路径
        """
        # 更新配置
        for key, value in kwargs.items():
            self.config[key] = value
        
        # 解析格式
        if output_format:
            self.config["output_format"] = output_format
        output_format = self.config.get("output_format", "txt")
        
        # 读取文件
        self.logger.info(f"读取文件: {file_path}")
        text = read_text_file(file_path)
        
        # 处理文本
        document = process_novel_text(text)
        
        # 设置语言
        document.source_language = self.config.get("source_language", "zh")
        document.target_language = self.config.get("target_language", "en")
        
        # 设置文档标题
        if "title" in kwargs:
            document.title = kwargs["title"]
        else:
            # 使用文件名作为标题
            base_name = os.path.basename(file_path)
            document.title = os.path.splitext(base_name)[0]
        
        # 保存进度文件路径
        progress_file = self.progress_dir / f"{document.id}_progress.json"
        
        # 翻译文档
        self.translate_document(document)
        
        # 导出文档
        output_path = self._export_document(document, output_format)
        
        return output_path
    
    def translate_document(self, document: Document) -> Document:
        """
        翻译文档
        
        Args:
            document: 文档对象
            
        Returns:
            翻译后的文档对象
        """
        self.current_document = document
        
        # 检查预算限制
        budget_limit = self.config.get("budget_limit", 0)
        if budget_limit > 0:
            cost_info = estimate_translation_cost(document, self.engine.get_name())
            if cost_info["cost"] > budget_limit:
                raise ValueError(f"翻译成本({cost_info['cost']} {cost_info['currency']})超过预算限制({budget_limit} {cost_info['currency']})")
        
        # 进度保存频率
        save_interval = self.config.get("save_interval", 1)
        progress_file = self.progress_dir / f"{document.id}_progress.json"
        
        # 翻译开始时间
        start_time = time.time()
        
        # 记录已处理的段落数
        processed_count = 0
        
        # 获取需要翻译的段落
        paragraphs_to_translate = []
        for para_id, para in sorted(document.paragraphs.items(), key=lambda x: x[0]):
            if not para.is_translated:
                paragraphs_to_translate.append(para)
        
        # 显示翻译信息
        total_chars = sum(len(p.content) for p in paragraphs_to_translate)
        cost_info = estimate_translation_cost(document, self.engine.get_name())
        self.logger.info(f"即将翻译{len(paragraphs_to_translate)}个段落，约{total_chars}个字符")
        self.logger.info(f"预计成本: {cost_info['cost']} {cost_info['currency']}")
        
        # 并行翻译
        parallel_requests = min(self.config.get("parallel_requests", 3), 10)
        batch_size = self.config.get("batch_size", 5)
        
        # 按批次进行翻译
        batches = [paragraphs_to_translate[i:i+batch_size] for i in range(0, len(paragraphs_to_translate), batch_size)]
        
        # 翻译进度条
        total_paragraphs = len(paragraphs_to_translate)
        with tqdm(total=total_paragraphs, desc="翻译进度") as pbar:
            for batch in batches:
                # 通知进度
                if self.progress_callback:
                    # 如果进度回调返回False，则暂停翻译
                    current_text = batch[0].content if batch else ""
                    if not self.progress_callback(processed_count, total_paragraphs, current_text):
                        self.logger.info("翻译已暂停")
                        # 等待继续信号
                        while True:
                            time.sleep(0.5)
                            if self.progress_callback(processed_count, total_paragraphs, current_text):
                                self.logger.info("翻译已恢复")
                                break
                
                # 翻译批次
                self._translate_batch(document, batch)
                
                # 更新进度
                processed_count += len(batch)
                pbar.update(len(batch))
                
                # 保存进度
                if processed_count % save_interval == 0 or processed_count == total_paragraphs:
                    document.save_progress(progress_file)
        
        # 翻译结束时间
        end_time = time.time()
        duration = end_time - start_time
        
        # 生成报告
        report_path = os.path.join(self.config.get("output_dir", "output"), f"{document.id}_report.md")
        report = generate_translation_report(document, cost_info, duration)
        write_text_file(report_path, report)
        
        # 清除当前文档引用
        self.current_document = None
        
        self.logger.info(f"翻译完成，耗时: {duration:.2f}秒")
        self.logger.info(f"翻译报告已保存至: {report_path}")
        
        return document
    
    def _translate_batch(self, document: Document, paragraphs: List[Paragraph]) -> None:
        """
        翻译段落批次
        
        Args:
            document: 文档对象
            paragraphs: 段落列表
        """
        # 翻译前处理
        contents = []
        for para in paragraphs:
            # 按术语表替换内容
            content = para.content
            for term, replacement in self.glossary.items():
                content = content.replace(term, f"<term>{replacement}</term>")
            contents.append(content)
        
        # 调用批量翻译
        try:
            translated = self.engine.batch_translate(contents)
            
            # 处理翻译结果
            for i, para in enumerate(paragraphs):
                # 记录翻译状态
                para.translated = translated[i]
                para.is_translated = True
                para.translation_time = time.time()
                
                # 恢复术语标记
                for term, replacement in self.glossary.items():
                    para.translated = para.translated.replace(f"<term>{replacement}</term>", replacement)
                
                # 更新文档中的段落
                document.paragraphs[para.id] = para
                
                # 通知进度回调当前段落已翻译
                if self.progress_callback and i < len(paragraphs) - 1:
                    next_para = paragraphs[i + 1].content if i + 1 < len(paragraphs) else ""
                    self.progress_callback(
                        sum(1 for p in document.paragraphs.values() if p.is_translated),
                        len(document.paragraphs),
                        next_para
                    )
        except Exception as e:
            self.logger.error(f"翻译批次失败: {e}")
            # 标记失败
            for para in paragraphs:
                para.attempts += 1
    
    def _export_document(self, document: Document, output_format: str) -> str:
        """
        导出文档
        
        Args:
            document: 文档对象
            output_format: 输出格式
            
        Returns:
            输出文件路径
        """
        # 获取格式处理函数
        formatter = get_formatter(output_format)
        
        # 构建输出路径
        output_dir = self.config.get("output_dir", "output")
        output_filename = f"{document.title}_{document.target_language}.{output_format}"
        output_path = os.path.join(output_dir, output_filename)
        
        # 构建格式选项
        options = {
            "bilingual_output": self.config.get("bilingual_output", False),
            "include_titles": True,
            "author": self.config.get("author", "Novel Translator"),
            "language": document.target_language,
        }
        
        # 导出文档
        self.logger.info(f"导出文档: {output_path}")
        output_path = formatter(document, options, output_path)
        
        return output_path
    
    def _handle_interrupt(self, signum, frame):
        """
        处理中断信号
        
        Args:
            signum: 信号编号
            frame: 当前帧
        """
        self.logger.warning("接收到中断信号，保存进度并退出...")
        
        # 保存当前文档进度
        if self.current_document:
            progress_file = self.progress_dir / f"{self.current_document.id}_progress.json"
            self.current_document.save_progress(progress_file)
            self.logger.info(f"进度已保存至: {progress_file}")
        
        sys.exit(0)

def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(description="小说翻译工具")
    
    # 添加参数
    parser.add_argument("file", help="输入文件路径")
    parser.add_argument("-o", "--output", help="输出格式", choices=list(list_formats().keys()), default="txt")
    parser.add_argument("-s", "--source", help="源语言", default="zh")
    parser.add_argument("-t", "--target", help="目标语言", default="en")
    parser.add_argument("-e", "--engine", help="翻译引擎", choices=list(list_engines().keys()), default="caiyun")
    parser.add_argument("-b", "--bilingual", help="双语模式", action="store_true")
    parser.add_argument("-g", "--glossary", help="术语表文件路径")
    parser.add_argument("--title", help="文档标题，不指定则使用文件名")
    parser.add_argument("--budget", help="预算限制", type=float, default=0)
    
    args = parser.parse_args()
    
    # 构建配置
    config = DEFAULT_CONFIG.copy()
    config.update({
        "source_language": args.source,
        "target_language": args.target,
        "default_engine": args.engine,
        "bilingual_output": args.bilingual,
        "budget_limit": args.budget,
    })
    
    if args.glossary:
        config["glossary_file"] = args.glossary
    
    if args.title:
        config["title"] = args.title
    
    # 创建翻译器
    translator = NovelTranslator(config)
    
    # 翻译文件
    output_path = translator.translate_file(args.file, args.output)
    
    print(f"翻译完成，输出文件: {output_path}")

if __name__ == "__main__":
    main() 