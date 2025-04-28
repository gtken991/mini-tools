# 小说翻译工具

小说翻译工具是一个支持多种翻译引擎和输出格式的文本翻译系统，专为翻译小说和长文本设计。支持将中文翻译成多种目标语言，也支持其他语言之间的互译。

## 功能特点

- **多引擎支持**：支持彩云小译、OpenAI等多种翻译引擎
- **多格式输出**：支持TXT、EPUB、DOCX等多种输出格式
- **章节自动识别**：自动识别并保持原文章节结构
- **术语表支持**：自定义专有名词翻译，保持术语一致性
- **双语对照**：支持生成双语对照版本，便于学习或对照阅读
- **进度保存**：支持中断后继续翻译，不丢失进度
- **图形界面**：提供友好的图形界面，简单易用

## 目录结构

- `src/` - 核心源代码
- `config/` - 配置文件
- `examples/` - 示例代码和文件
- `docs/` - 文档
- `dist/` - 可执行文件和打包脚本

## 使用方式

本工具提供两种使用方式：

### 1. 对于非编程用户

使用预编译的可执行文件，通过图形界面操作：

- **Windows**: 双击`dist/windows/小说翻译工具.exe`
- **macOS**: 打开`dist/macos/小说翻译工具.app`

### 2. 对于开发者

通过Python API或命令行方式使用：

```python
from tools.novel_translator.src import NovelTranslator

# 创建翻译器
translator = NovelTranslator()
# 翻译文件
output_file = translator.translate_file("novel.txt", "txt")
```

命令行方式：

```bash
python -m tools.novel_translator.src.cli novel.txt -s zh -t en -e openai -o epub
```

## 文档

- [用户手册](docs/用户手册.md) - 面向普通用户的使用说明
- [快速入门指南](docs/快速入门指南.md) - 快速上手指南
- [开发指南](docs/开发指南.md) - 面向开发者的二次开发说明

## 安装

### 非编程用户

从[发布页面](https://github.com/yourusername/novel-translator/releases)下载最新版本的预编译可执行文件。

### 开发者

克隆代码库并安装依赖：

```bash
git clone https://github.com/yourusername/novel-translator.git
cd novel-translator
pip install -r requirements.txt
```

## API密钥

使用前需要配置API密钥：

1. 复制`config/config.env.example`为`.env`
2. 编辑`.env`文件，填入您的API密钥

获取API密钥的方法：
- [彩云小译](https://platform.caiyunapp.com/login)
- [OpenAI](https://platform.openai.com/signup)

## 打包与发布

- Windows打包：`python dist/pyinstaller_win.py`
- macOS打包：`python dist/py2app_mac.py`

## 许可证

MIT License

## 贡献

欢迎提交Issues和Pull Requests！ 