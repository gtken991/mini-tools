#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小说翻译工具图形界面
"""

import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinter.font import Font
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import queue

# 导入翻译工具相关模块
from .translator import NovelTranslator
from .engines import list_engines
from .output_formats import list_formats
from .config import DEFAULT_CONFIG, LANGUAGE_MAP
from .utils import detect_file_encoding, read_text_file
from . import __version__

# 创建消息队列，用于线程间通信
message_queue = queue.Queue()

class TranslationProgress:
    """翻译进度类，用于在GUI和翻译线程之间共享进度信息"""
    def __init__(self):
        self.total_paragraphs = 0
        self.translated_paragraphs = 0
        self.current_paragraph = ""
        self.is_running = False
        self.is_cancelled = False
        self.is_paused = False
        self.start_time = 0
        self.end_time = 0
        self.error = None

class NovelTranslatorGUI:
    """小说翻译工具图形界面"""
    def __init__(self, root):
        """初始化界面"""
        self.root = root
        self.root.title(f"小说翻译工具 v{__version__}")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # 设置图标（如果有）
        # self.root.iconbitmap("icon.ico")
        
        # 设置字体
        self.default_font = Font(family="Microsoft YaHei", size=10)
        self.title_font = Font(family="Microsoft YaHei", size=12, weight="bold")
        
        # 初始化变量
        self.input_file = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.output_format = tk.StringVar(value="txt")
        self.engine = tk.StringVar(value="caiyun")
        self.source_lang = tk.StringVar(value="auto")
        self.target_lang = tk.StringVar(value="en")
        self.glossary_file = tk.StringVar()
        self.is_bilingual = tk.BooleanVar(value=False)
        self.context_level = tk.IntVar(value=1)
        self.document_title = tk.StringVar()
        self.budget_limit = tk.DoubleVar(value=0)
        
        # 翻译进度和线程
        self.progress = TranslationProgress()
        self.translation_thread = None
        self.progress_update_id = None
        
        # 创建主框架
        self.create_main_frame()
        
        # 开始GUI更新循环
        self.update_from_queue()
        
    def create_main_frame(self):
        """创建主框架"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建顶部文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="文件选择", padding="10")
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 输入文件
        ttk.Label(file_frame, text="输入文件:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(file_frame, textvariable=self.input_file, width=50).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Button(file_frame, text="浏览...", command=self.browse_input_file).grid(row=0, column=2, padx=5, pady=5)
        
        # 输出目录
        ttk.Label(file_frame, text="输出目录:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(file_frame, textvariable=self.output_dir, width=50).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Button(file_frame, text="浏览...", command=self.browse_output_dir).grid(row=1, column=2, padx=5, pady=5)
        
        # 术语表文件
        ttk.Label(file_frame, text="术语表文件:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(file_frame, textvariable=self.glossary_file, width=50).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Button(file_frame, text="浏览...", command=self.browse_glossary_file).grid(row=2, column=2, padx=5, pady=5)
        
        # 文档标题
        ttk.Label(file_frame, text="文档标题:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(file_frame, textvariable=self.document_title, width=50).grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Label(file_frame, text="(可选，默认使用文件名)").grid(row=3, column=2, sticky=tk.W, padx=5, pady=5)
        
        # 设置列权重
        file_frame.columnconfigure(1, weight=1)
        
        # 创建翻译设置区域
        settings_frame = ttk.LabelFrame(main_frame, text="翻译设置", padding="10")
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 翻译引擎
        ttk.Label(settings_frame, text="翻译引擎:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        engines = list(list_engines().keys())
        ttk.Combobox(settings_frame, textvariable=self.engine, values=engines, state="readonly").grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # 源语言
        ttk.Label(settings_frame, text="源语言:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        languages = ["auto"] + list(LANGUAGE_MAP.keys())
        ttk.Combobox(settings_frame, textvariable=self.source_lang, values=languages, state="readonly").grid(row=0, column=3, sticky=tk.EW, padx=5, pady=5)
        
        # 目标语言
        ttk.Label(settings_frame, text="目标语言:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Combobox(settings_frame, textvariable=self.target_lang, values=list(LANGUAGE_MAP.keys()), state="readonly").grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # 输出格式
        ttk.Label(settings_frame, text="输出格式:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        formats = list(list_formats().keys())
        ttk.Combobox(settings_frame, textvariable=self.output_format, values=formats, state="readonly").grid(row=1, column=3, sticky=tk.EW, padx=5, pady=5)
        
        # 上下文级别
        ttk.Label(settings_frame, text="上下文级别:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Combobox(settings_frame, textvariable=self.context_level, values=["0 (无上下文)", "1 (段落级)", "2 (章节级)", "3 (全文级)"], state="readonly").grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # 预算限制
        ttk.Label(settings_frame, text="预算限制:").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        budget_frame = ttk.Frame(settings_frame)
        budget_frame.grid(row=2, column=3, sticky=tk.EW, padx=5, pady=5)
        ttk.Entry(budget_frame, textvariable=self.budget_limit, width=10).pack(side=tk.LEFT)
        ttk.Label(budget_frame, text="元 (0表示无限制)").pack(side=tk.LEFT, padx=5)
        
        # 是否双语输出
        ttk.Checkbutton(settings_frame, text="双语对照输出", variable=self.is_bilingual).grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # 设置列权重
        settings_frame.columnconfigure(1, weight=1)
        settings_frame.columnconfigure(3, weight=1)
        
        # 创建预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="内容预览", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD, width=80, height=10)
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.preview_text.insert(tk.END, "选择文件后将显示内容预览...")
        self.preview_text.config(state=tk.DISABLED)
        
        # 创建进度区域
        progress_frame = ttk.LabelFrame(main_frame, text="翻译进度", padding="10")
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 进度条
        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        # 进度信息
        self.progress_info = ttk.Label(progress_frame, text="准备就绪")
        self.progress_info.pack(fill=tk.X, padx=5, pady=5)
        
        # 当前翻译段落
        self.current_para_label = ttk.Label(progress_frame, text="")
        self.current_para_label.pack(fill=tk.X, padx=5, pady=5)
        
        # 创建按钮区域
        button_frame = ttk.Frame(main_frame, padding="10")
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 按钮
        self.start_button = ttk.Button(button_frame, text="开始翻译", command=self.start_translation)
        self.start_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.pause_button = ttk.Button(button_frame, text="暂停", command=self.pause_translation, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.cancel_button = ttk.Button(button_frame, text="取消", command=self.cancel_translation, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, width=80, height=8)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
        # 输入文件变更事件
        self.input_file.trace_add("write", self.on_input_file_change)
        
    def browse_input_file(self):
        """浏览并选择输入文件"""
        file_path = filedialog.askopenfilename(
            title="选择小说文件",
            filetypes=[("文本文件", "*.txt"), ("Markdown文件", "*.md"), ("所有文件", "*.*")]
        )
        if file_path:
            self.input_file.set(file_path)
            
            # 自动设置输出目录
            dir_path = os.path.dirname(file_path)
            if not self.output_dir.get():
                self.output_dir.set(dir_path)
                
            # 自动设置文档标题
            file_name = os.path.basename(file_path)
            name_without_ext = os.path.splitext(file_name)[0]
            if not self.document_title.get():
                self.document_title.set(name_without_ext)
    
    def browse_output_dir(self):
        """浏览并选择输出目录"""
        dir_path = filedialog.askdirectory(title="选择输出目录")
        if dir_path:
            self.output_dir.set(dir_path)
    
    def browse_glossary_file(self):
        """浏览并选择术语表文件"""
        file_path = filedialog.askopenfilename(
            title="选择术语表文件",
            filetypes=[("CSV文件", "*.csv"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            self.glossary_file.set(file_path)
    
    def on_input_file_change(self, *args):
        """输入文件变更事件处理"""
        file_path = self.input_file.get()
        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                # 读取文件部分内容进行预览
                encoding = detect_file_encoding(file_path)
                preview_text = read_text_file(file_path, limit=10)
                
                # 更新预览区域
                self.preview_text.config(state=tk.NORMAL)
                self.preview_text.delete(1.0, tk.END)
                self.preview_text.insert(tk.END, f"文件编码: {encoding}\n\n")
                for line in preview_text:
                    if line.strip():
                        preview = line[:100] + ('...' if len(line) > 100 else '')
                        self.preview_text.insert(tk.END, preview + "\n\n")
                self.preview_text.config(state=tk.DISABLED)
                
                # 记录日志
                self.log(f"已加载文件: {file_path}")
                self.log(f"文件编码: {encoding}")
                
            except Exception as e:
                self.log(f"读取文件出错: {e}", error=True)
    
    def log(self, message, error=False):
        """添加日志"""
        self.log_text.config(state=tk.NORMAL)
        if error:
            self.log_text.insert(tk.END, f"[错误] {message}\n")
        else:
            self.log_text.insert(tk.END, f"[信息] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def start_translation(self):
        """开始翻译"""
        # 检查输入文件
        if not self.input_file.get() or not os.path.exists(self.input_file.get()):
            messagebox.showerror("错误", "请选择有效的输入文件")
            return
        
        # 检查输出目录
        output_dir = self.output_dir.get()
        if not output_dir:
            output_dir = os.path.dirname(self.input_file.get())
            self.output_dir.set(output_dir)
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("错误", f"创建输出目录失败: {e}")
                return
        
        # 术语表检查
        if self.glossary_file.get() and not os.path.exists(self.glossary_file.get()):
            messagebox.showerror("错误", "所选术语表文件不存在")
            return
        
        # 重置进度
        self.progress = TranslationProgress()
        self.progress.is_running = True
        self.progress.start_time = time.time()
        
        # 更新UI状态
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.NORMAL)
        self.progress_bar["value"] = 0
        self.progress_info.config(text="准备翻译...")
        self.current_para_label.config(text="")
        
        # 获取翻译参数
        params = {
            "input_file": self.input_file.get(),
            "output_dir": self.output_dir.get(),
            "output_format": self.output_format.get(),
            "engine_name": self.engine.get(),
            "source_lang": self.source_lang.get(),
            "target_lang": self.target_lang.get(),
            "glossary_file": self.glossary_file.get() if self.glossary_file.get() else None,
            "title": self.document_title.get() if self.document_title.get() else None,
            "bilingual": self.is_bilingual.get(),
            "context_level": self.context_level.get(),
            "budget_limit": self.budget_limit.get()
        }
        
        # 记录日志
        self.log("开始翻译任务")
        self.log(f"引擎: {params['engine_name']}, 源语言: {params['source_lang']}, 目标语言: {params['target_lang']}")
        
        # 创建并启动翻译线程
        self.translation_thread = threading.Thread(target=self.translation_worker, args=(params,))
        self.translation_thread.daemon = True
        self.translation_thread.start()
        
        # 开始更新进度
        self.update_progress()
    
    def translation_worker(self, params):
        """翻译线程"""
        try:
            # 创建翻译器配置
            config = DEFAULT_CONFIG.copy()
            config.update({
                "default_engine": params["engine_name"],
                "source_language": params["source_lang"],
                "target_language": params["target_lang"],
                "glossary_file": params["glossary_file"],
                "context_level": params["context_level"],
                "bilingual_output": params["bilingual"],
                "budget_limit": params["budget_limit"],
                "output_dir": params["output_dir"]
            })
            
            # 创建翻译器
            translator = NovelTranslator(config)
            
            # 自定义进度回调
            def progress_callback(current, total, text=""):
                if self.progress.is_cancelled:
                    return False  # 返回False停止翻译
                
                self.progress.total_paragraphs = total
                self.progress.translated_paragraphs = current
                self.progress.current_paragraph = text
                
                message_queue.put(("progress", {
                    "current": current,
                    "total": total,
                    "text": text
                }))
                
                return not self.progress.is_paused  # 如果暂停则返回False
            
            # 设置进度回调
            translator.set_progress_callback(progress_callback)
            
            # 翻译文件
            output_file = translator.translate_file(
                params["input_file"],
                params["output_format"],
                title=params["title"]
            )
            
            # 完成
            self.progress.end_time = time.time()
            message_queue.put(("complete", {"output_file": output_file}))
            
        except Exception as e:
            # 错误
            self.progress.error = str(e)
            message_queue.put(("error", {"message": str(e)}))
    
    def update_from_queue(self):
        """从队列更新UI"""
        try:
            while not message_queue.empty():
                message_type, data = message_queue.get_nowait()
                
                if message_type == "progress":
                    # 更新进度
                    current = data["current"]
                    total = data["total"]
                    text = data["text"]
                    
                    # 更新进度条
                    if total > 0:
                        percent = int(current / total * 100)
                        self.progress_bar["value"] = percent
                        elapsed = time.time() - self.progress.start_time
                        if current > 0:
                            remaining = elapsed / current * (total - current)
                            self.progress_info.config(text=f"进度: {current}/{total} ({percent}%) - 剩余时间: {int(remaining)}秒")
                        else:
                            self.progress_info.config(text=f"进度: {current}/{total} ({percent}%)")
                    
                    # 更新当前段落信息
                    if text:
                        preview = text[:50] + ('...' if len(text) > 50 else '')
                        self.current_para_label.config(text=f"当前段落: {preview}")
                    
                elif message_type == "complete":
                    # 翻译完成
                    output_file = data["output_file"]
                    self.progress_bar["value"] = 100
                    duration = self.progress.end_time - self.progress.start_time
                    self.progress_info.config(text=f"翻译完成 - 用时: {int(duration)}秒")
                    self.current_para_label.config(text="")
                    
                    # 恢复UI状态
                    self.progress.is_running = False
                    self.start_button.config(state=tk.NORMAL)
                    self.pause_button.config(state=tk.DISABLED)
                    self.cancel_button.config(state=tk.DISABLED)
                    
                    # 记录日志
                    self.log(f"翻译完成，用时: {int(duration)}秒")
                    self.log(f"输出文件: {output_file}")
                    
                    # 提示用户
                    messagebox.showinfo("翻译完成", f"翻译任务已完成!\n输出文件: {output_file}")
                    
                elif message_type == "error":
                    # 翻译错误
                    error_message = data["message"]
                    self.progress.is_running = False
                    self.start_button.config(state=tk.NORMAL)
                    self.pause_button.config(state=tk.DISABLED)
                    self.cancel_button.config(state=tk.DISABLED)
                    
                    # 记录日志
                    self.log(f"翻译出错: {error_message}", error=True)
                    
                    # 提示用户
                    messagebox.showerror("翻译错误", f"翻译过程中出错:\n{error_message}")
                
        except queue.Empty:
            pass
        
        # 继续队列检查
        self.root.after(100, self.update_from_queue)
    
    def update_progress(self):
        """更新进度显示"""
        if self.progress.is_running:
            # 更新进度显示，每100毫秒更新一次
            self.root.after(100, self.update_progress)
    
    def pause_translation(self):
        """暂停翻译"""
        if self.progress.is_running:
            if self.progress.is_paused:
                # 恢复翻译
                self.progress.is_paused = False
                self.pause_button.config(text="暂停")
                self.log("翻译已恢复")
            else:
                # 暂停翻译
                self.progress.is_paused = True
                self.pause_button.config(text="继续")
                self.log("翻译已暂停")
    
    def cancel_translation(self):
        """取消翻译"""
        if self.progress.is_running:
            if messagebox.askyesno("确认", "确定要取消翻译吗?"):
                self.progress.is_cancelled = True
                self.progress.is_running = False
                
                # 恢复UI状态
                self.start_button.config(state=tk.NORMAL)
                self.pause_button.config(state=tk.DISABLED)
                self.cancel_button.config(state=tk.DISABLED)
                
                # 记录日志
                self.log("翻译已取消")
                self.progress_info.config(text="翻译已取消")

def main():
    """主函数"""
    root = tk.Tk()
    app = NovelTranslatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 