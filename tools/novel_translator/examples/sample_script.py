#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
小说翻译工具示例脚本
用法：python sample_script.py [参数]
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from colorama import init, Fore, Style

# 将当前目录添加到路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# 导入翻译工具模块
from tools.novel_translator import NovelTranslator
from tools.novel_translator.utils import detect_file_encoding, read_text_file

# 初始化colorama
init()

def print_colored(text, color=Fore.WHITE, style=Style.NORMAL):
    """打印彩色文本"""
    print(f"{style}{color}{text}{Style.RESET_ALL}")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='小说翻译工具示例脚本')
    parser.add_argument('file', nargs='?', help='输入文件路径')
    parser.add_argument('-s', '--source-lang', default='auto', help='源语言 (auto, en, zh, ja, ...)')
    parser.add_argument('-t', '--target-lang', default='zh-cn', help='目标语言 (zh-cn, en, ja, ...)')
    parser.add_argument('-e', '--engine', default='caiyun', choices=['caiyun', 'openai'], help='翻译引擎')
    parser.add_argument('-o', '--output-format', default='txt', choices=['txt', 'epub', 'docx'], help='输出格式')
    parser.add_argument('-b', '--bilingual', action='store_true', help='是否生成双语对照版本')
    parser.add_argument('-g', '--glossary', help='术语表文件路径')
    parser.add_argument('--title', help='文档标题 (默认使用文件名)')
    parser.add_argument('--budget', type=float, default=float('inf'), help='翻译预算上限（元）')
    
    return parser.parse_args()

def main():
    """主函数"""
    # 加载环境变量
    load_dotenv()
    
    # 解析命令行参数
    args = parse_args()
    
    # 如果没有提供文件参数，显示使用方法
    if not args.file:
        print_colored("请提供输入文件路径！", Fore.RED, Style.BRIGHT)
        print("示例: python sample_script.py novel.txt -t en -e openai -o epub")
        return
    
    # 检查文件是否存在
    if not os.path.exists(args.file):
        print_colored(f"错误: 找不到文件 {args.file}", Fore.RED, Style.BRIGHT)
        return
    
    # 检测文件编码并读取部分内容预览
    encoding = detect_file_encoding(args.file)
    preview_text = read_text_file(args.file, encoding=encoding, limit=10)
    
    # 确定文档标题
    document_title = args.title or os.path.splitext(os.path.basename(args.file))[0]
    
    # 显示翻译配置信息
    print_colored("\n===== 小说翻译工具 =====", Fore.CYAN, Style.BRIGHT)
    print_colored(f"输入文件: {args.file}", Fore.YELLOW)
    print_colored(f"文件编码: {encoding}", Fore.YELLOW)
    print_colored(f"文档标题: {document_title}", Fore.YELLOW)
    print_colored(f"源语言: {args.source_lang}", Fore.YELLOW)
    print_colored(f"目标语言: {args.target_lang}", Fore.YELLOW)
    print_colored(f"翻译引擎: {args.engine}", Fore.YELLOW)
    print_colored(f"输出格式: {args.output_format}", Fore.YELLOW)
    print_colored(f"双语对照: {'是' if args.bilingual else '否'}", Fore.YELLOW)
    print_colored(f"术语表: {args.glossary if args.glossary else '未使用'}", Fore.YELLOW)
    print_colored(f"预算上限: {args.budget if args.budget != float('inf') else '无限制'} 元", Fore.YELLOW)
    
    print_colored("\n文件内容预览:", Fore.GREEN)
    for line in preview_text:
        if line.strip():
            print(f"  {line[:100]}{'...' if len(line) > 100 else ''}")
    
    # 询问用户是否继续
    print_colored("\n是否开始翻译? (y/n): ", Fore.CYAN, Style.BRIGHT, end="")
    choice = input().lower()
    if choice != 'y':
        print_colored("已取消翻译", Fore.RED)
        return
    
    try:
        # 创建翻译器实例
        translator = NovelTranslator(
            source_lang=args.source_lang,
            target_lang=args.target_lang,
            engine_name=args.engine,
            glossary_file=args.glossary,
            budget_limit=args.budget
        )
        
        # 翻译文件
        output_file = translator.translate_file(
            input_file=args.file,
            output_format=args.output_format,
            title=document_title,
            bilingual=args.bilingual
        )
        
        # 显示完成信息
        print_colored("\n翻译完成！", Fore.GREEN, Style.BRIGHT)
        print_colored(f"输出文件: {output_file}", Fore.YELLOW)
        
    except Exception as e:
        print_colored(f"\n翻译过程中出错: {str(e)}", Fore.RED, Style.BRIGHT)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 