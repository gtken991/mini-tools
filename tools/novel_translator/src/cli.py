#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from .translator import NovelTranslator
from .models import Document
from .config import load_config, save_config, TranslationConfig
from .utils import detect_file_encoding, read_text_file
from . import __version__

def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='小说翻译工具 - 支持多种翻译引擎和输出格式',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('input_file', help='输入文件路径', nargs='?')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('-f', '--format', choices=['txt', 'epub', 'docx'], default='txt',
                       help='输出格式 (默认: txt)')
    parser.add_argument('-e', '--engine', help='翻译引擎 (caiyun, openai, papago, deepl等)')
    parser.add_argument('-s', '--source-lang', help='源语言')
    parser.add_argument('-t', '--target-lang', help='目标语言')
    parser.add_argument('-g', '--glossary', help='术语表文件路径')
    parser.add_argument('-c', '--config', help='指定配置文件路径')
    parser.add_argument('--context-level', type=int, choices=[0, 1, 2, 3], 
                       help='上下文模式 (0:无 1:段落 2:章节 3:全文)')
    parser.add_argument('--save-config', action='store_true', 
                       help='将当前参数保存为默认配置')
    parser.add_argument('--batch', action='store_true',
                       help='批量模式，输入参数为包含多个文件的目录')
    parser.add_argument('--verbose', '-v', action='count', default=0,
                       help='详细输出模式')
    parser.add_argument('--version', action='version',
                       version=f'小说翻译工具 v{__version__}')
    
    return parser

def validate_args(args: argparse.Namespace) -> Tuple[bool, str]:
    """验证命令行参数的有效性"""
    if not args.input_file and not args.save_config:
        return False, "错误: 必须提供输入文件路径或使用--save-config选项"
    
    if args.input_file:
        path = Path(args.input_file)
        if not path.exists():
            return False, f"错误: 输入文件 '{args.input_file}' 不存在"
        
        if args.batch and not path.is_dir():
            return False, f"错误: 批量模式下，输入路径必须是目录"
        elif not args.batch and not path.is_file():
            return False, f"错误: 输入路径必须是文件"
    
    if args.glossary and not Path(args.glossary).exists():
        return False, f"错误: 术语表文件 '{args.glossary}' 不存在"
    
    return True, ""

def get_output_path(input_path: str, output_path: Optional[str], format: str) -> str:
    """根据输入路径和格式生成输出路径"""
    if output_path:
        return output_path
    
    input_file = Path(input_path)
    stem = input_file.stem
    return str(input_file.parent / f"{stem}_翻译.{format}")

def process_file(translator: NovelTranslator, input_path: str, 
                output_path: str, output_format: str, verbose: int) -> bool:
    """处理单个文件的翻译"""
    try:
        if verbose:
            print(f"正在翻译: {input_path} -> {output_path}")
        
        start_time = time.time()
        translator.translate_file(input_path, output_path, output_format)
        end_time = time.time()
        
        if verbose:
            print(f"翻译完成，用时 {end_time - start_time:.2f} 秒")
        return True
    except Exception as e:
        print(f"翻译出错: {e}")
        if verbose > 1:
            import traceback
            traceback.print_exc()
        return False

def batch_process(translator: NovelTranslator, input_dir: str, 
                 output_dir: Optional[str], output_format: str, verbose: int) -> Tuple[int, int]:
    """批量处理目录中的所有文本文件"""
    input_path = Path(input_dir)
    output_path = Path(output_dir) if output_dir else input_path
    
    # 确保输出目录存在
    output_path.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    fail_count = 0
    
    # 查找所有文本文件
    extensions = ['.txt', '.md']
    files = []
    for ext in extensions:
        files.extend(input_path.glob(f"*{ext}"))
    
    total_files = len(files)
    if verbose:
        print(f"找到 {total_files} 个文件需要翻译")
    
    for i, file in enumerate(files, 1):
        if verbose:
            print(f"[{i}/{total_files}] 处理文件: {file.name}")
        
        output_file = output_path / f"{file.stem}_翻译.{output_format}"
        
        if process_file(translator, str(file), str(output_file), output_format, verbose):
            success_count += 1
        else:
            fail_count += 1
    
    return success_count, fail_count

def main() -> int:
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 加载配置
    config_path = args.config
    config = load_config(config_path)
    
    # 用命令行参数覆盖配置
    if args.engine:
        config.engine = args.engine
    if args.source_lang:
        config.source_lang = args.source_lang
    if args.target_lang:
        config.target_lang = args.target_lang
    if args.glossary:
        config.glossary_path = args.glossary
    if args.context_level is not None:
        config.context_level = args.context_level
    
    # 保存配置（如果需要）
    if args.save_config:
        save_config(config, config_path)
        print(f"配置已保存")
        if not args.input_file:
            return 0
    
    # 验证参数
    valid, message = validate_args(args)
    if not valid:
        print(message)
        return 1
    
    try:
        # 创建翻译器
        translator = NovelTranslator(config)
        
        if args.batch:
            # 批量处理
            output_dir = args.output
            success, fail = batch_process(
                translator, 
                args.input_file, 
                output_dir, 
                args.format, 
                args.verbose
            )
            print(f"批量翻译完成: {success} 个成功, {fail} 个失败")
        else:
            # 单文件处理
            output_path = get_output_path(args.input_file, args.output, args.format)
            success = process_file(
                translator, 
                args.input_file, 
                output_path, 
                args.format, 
                args.verbose
            )
            if success:
                print(f"翻译完成: {output_path}")
                return 0
            else:
                return 1
    
    except KeyboardInterrupt:
        print("\n翻译被用户中断")
        return 130
    except Exception as e:
        print(f"发生错误: {e}")
        if args.verbose > 1:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 