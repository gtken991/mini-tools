# File Archiver

A powerful Python tool for organizing and archiving files based on type, date, and other criteria.

## Features

- Multi-source directory organization
- Automatic classification by type and date
- File deduplication with MD5 hash
- File integrity verification
- Configurable backup options
- Detailed logging
- Error handling and recovery

## ⚠️ Important Notes

- **Original Files**: By default, the tool **preserves** original files after archiving. If you want to delete original files after successful archiving, you need to explicitly set `keep_original: false` in the backup section of the configuration.
- File integrity is always verified after copying
- Duplicate files are detected using MD5 hash
- Logs are saved in the logs directory

## File Types Supported

- Images: jpg, jpeg, png, gif, webp, bmp
- Documents: pdf, docx, doc, xlsx, pptx, txt, md
- Videos: mp4, mov, mkv, avi, wmv
- Audio: mp3, wav, m4a, flac, ogg
- Archives: zip, rar, 7z, tar.gz, gz
- Code: py, js, java, cpp, html, css, json
- Others: Any unrecognized extensions

## Requirements

- Python 3.10+
- See requirements.txt for detailed dependencies

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Configuration

1. Copy the example configuration:
```bash
cp config.example.json config.json
```

2. Edit config.json to set your paths and preferences:

```json
{
    "source_directories": [
        "~/Documents"
    ],
    "target_directory": "~/Documents/Archived_Files",
    "organization": {
        "by_date": true,           // Organize files by date
        "remove_duplicates": true   // Remove duplicate files
    },
    "file_types": {
        "images": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
        "documents": [".pdf", ".docx", ".doc", ".xlsx", ".pptx", ".txt", ".md"],
        "videos": [".mp4", ".mov", ".mkv", ".avi", ".wmv"],
        "audio": [".mp3", ".wav", ".m4a", ".flac", ".ogg"],
        "archives": [".zip", ".rar", ".7z", ".tar.gz", ".gz"],
        "code": [".py", ".js", ".java", ".cpp", ".html", ".css", ".json"]
    },
    "logging": {
        "level": "INFO",           // Log level: DEBUG, INFO, WARNING, ERROR
        "file": "./logs/file_archiver.log"  // Log file path
    },
    "backup": {
        "enabled": true,           // Enable backup functionality
        "keep_original": true,     // Keep original files after archiving
        "verify_copy": true        // Verify file integrity after copy
    },
    "processing": {
        "skip_hidden_files": true  // Skip hidden files during processing
    }
}
```

## Usage

1. Basic usage:
```python
from file_archiver import FileArchiver

# Create archiver instance
archiver = FileArchiver("config.json")
archiver.organize_files()
```

## Output Structure

```
Archived_Files/
├── images/
│   └── 2024/
│       └── 01/
│           ├── photo1.jpg
│           └── screenshot.png
├── documents/
│   └── 2024/
│       └── 01/
│           ├── report.pdf
│           └── notes.docx
└── others/
    └── 2024/
        └── 01/
```

## Error Handling

- File access errors are logged and reported
- Duplicate files are handled according to configuration
- Invalid paths are reported
- All errors are logged with detailed information

---

# 文件归档工具

这是一个强大的文件归档和组织工具，支持多种文件类型、自动分类、去重和备份功能。

## ⚠️ 重要说明

- **原始文件**：默认情况下，工具会**保留**归档后的原始文件。如果要在成功归档后删除原始文件，需要在配置文件的 backup 部分明确设置 `keep_original: false`。
- 每次复制后都会验证文件完整性
- 使用 MD5 哈希检测重复文件
- 日志文件保存在 logs 目录中

## 功能特性

- 多源目录文件整理
- 按类型和日期自动分类
- 基于 MD5 的文件去重
- 文件完整性验证
- 可配置的备份选项
- 详细的日志记录
- 错误处理和恢复

## 支持的文件类型

- 图片：jpg, jpeg, png, gif, webp, bmp
- 文档：pdf, docx, doc, xlsx, pptx, txt, md
- 视频：mp4, mov, mkv, avi, wmv
- 音频：mp3, wav, m4a, flac, ogg
- 压缩包：zip, rar, 7z, tar.gz, gz
- 代码：py, js, java, cpp, html, css, json
- 其他：任何未识别的扩展名

## 环境要求

- Python 3.10+
- 详细依赖见 requirements.txt

## 安装

```bash
# 安装依赖
pip install -r requirements.txt
```

## 配置

1. 复制示例配置文件：
```bash
cp config.example.json config.json
```

2. 编辑 config.json 设置路径和选项：

```json
{
    "source_directories": [
        "~/Documents"
    ],
    "target_directory": "~/Documents/Archived_Files",
    "organization": {
        "by_date": true,           // 是否按日期组织文件
        "remove_duplicates": true   // 是否删除重复文件
    },
    "file_types": {
        "images": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
        "documents": [".pdf", ".docx", ".doc", ".xlsx", ".pptx", ".txt", ".md"],
        "videos": [".mp4", ".mov", ".mkv", ".avi", ".wmv"],
        "audio": [".mp3", ".wav", ".m4a", ".flac", ".ogg"],
        "archives": [".zip", ".rar", ".7z", ".tar.gz", ".gz"],
        "code": [".py", ".js", ".java", ".cpp", ".html", ".css", ".json"]
    },
    "logging": {
        "level": "INFO",           // 日志级别：DEBUG, INFO, WARNING, ERROR
        "file": "./logs/file_archiver.log"  // 日志文件路径
    },
    "backup": {
        "enabled": true,           // 是否启用备份功能
        "keep_original": true,     // 是否保留原始文件
        "verify_copy": true        // 是否验证文件完整性
    },
    "processing": {
        "skip_hidden_files": true  // 是否跳过隐藏文件
    }
}
```

## 使用方法

1. 基本用法：
```python
from file_archiver import FileArchiver

# 创建归档工具实例
archiver = FileArchiver("config.json")
archiver.organize_files()
```

## 输出结构

```
Archived_Files/
├── images/          # 图片
│   └── 2024/
│       └── 01/
│           ├── photo1.jpg
│           └── screenshot.png
├── documents/       # 文档
│   └── 2024/
│       └── 01/
│           ├── report.pdf
│           └── notes.docx
└── others/          # 其他
    └── 2024/
        └── 01/
```

## 错误处理

- 文件访问错误会被记录和报告
- 根据配置处理重复文件
- 报告无效的路径
- 所有错误都会被详细记录