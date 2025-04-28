#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小说翻译工具GUI启动脚本
"""

import os
import sys
import tkinter as tk
import logging

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("novel_translator_gui")

# 将当前目录添加到路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

def main():
    """主函数"""
    try:
        # 尝试导入GUI模块
        try:
            # 优先从src导入
            from tools.novel_translator.src.gui import NovelTranslatorGUI
            logger.info("从src目录导入GUI模块成功")
        except ImportError:
            # 如果失败，尝试从主包导入
            from tools.novel_translator.gui import NovelTranslatorGUI
            logger.info("从主目录导入GUI模块成功")
            
        # 创建主窗口
        root = tk.Tk()
        app = NovelTranslatorGUI(root)
        
        # 打印欢迎信息
        print("========================================")
        print("欢迎使用小说翻译工具!")
        print("可通过界面选择文件并配置翻译设置")
        print("如需帮助请查看文档目录下的用户手册")
        print("========================================")
        
        root.mainloop()
    except ImportError as e:
        if "tkinter" in str(e).lower():
            print("错误: tkinter模块未安装。")
            print("在大多数Linux系统上，可以使用以下命令安装:")
            print("  Ubuntu/Debian: sudo apt-get install python3-tk")
            print("  CentOS/RHEL: sudo yum install python3-tkinter")
            print("  Arch Linux: sudo pacman -S tk")
            print("在macOS上，安装Python时通常已包含tkinter")
            print("在Windows上，安装Python时请确保选中了tcl/tk和IDLE选项")
        else:
            print(f"导入模块出错: {e}")
            import traceback
            traceback.print_exc()
    except Exception as e:
        print(f"启动GUI出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 