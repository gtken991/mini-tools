# Speech to Text Converter

A Python tool for converting speech audio files to text using various engines.

## Features

- Support multiple speech recognition engines:
  - Local processing (pocketsphinx)
  - Google Cloud Speech-to-Text
  - OpenAI Whisper (offline model)
- Multiple audio format support
- Configurable output formats
- Detailed logging

## Requirements

- Python 3.10+
- ffmpeg (system dependency)
- Other dependencies in requirements.txt

## Installation

1. Install system dependencies:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html and add to system PATH
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the example configuration:
```bash
cp config.example.json config.json
```

2. Configuration file explanation:
```json
{
    "input_directory": "./audio",      // Input audio directory
    "output_directory": "./transcripts", // Output text directory
    "model_directory": "./models",      // Whisper model storage
    "api_settings": {
        "provider": "whisper",          // Choose engine: local/whisper/google
        "credentials": {
            "whisper": {
                "model": "base",        // Model size: tiny/base/small/medium/large
                "language": "fr",       // Target language
                "update_model": false   // Whether to update model
            }
        }
    },
    "file_types": [                    // Supported audio formats
        ".wav",
        ".mp3",
        ".m4a",
        ".flac",
        ".ogg"
    ],
    "output_format": {
        "type": "txt",                 // Output file format
        "timestamp": true              // Include timestamps
    },
    "logging": {
        "level": "INFO",               // Log level
        "file": "speech_to_text.log"   // Log file
    }
}
```

### Whisper Model Details
| Model  | Size  | Required Memory | Relative Speed | Use Case |
|--------|-------|----------------|----------------|-----------|
| tiny   | 39M   | ~1GB           | ~32x           | Quick testing |
| base   | 74M   | ~1GB           | ~16x           | Simple cases |
| small  | 244M  | ~2GB           | ~6x            | General use |
| medium | 769M  | ~5GB           | ~2x            | Higher quality |
| large  | 1550M | ~10GB          | 1x             | Best quality |

## Security Notes

1. Configuration file security:
   - Don't commit config files with credentials
   - Add config.json to .gitignore

2. Model file management:
   - Models are stored in model_directory
   - Downloaded automatically on first run
   - Models are reusable, no need to re-download

## Usage

1. Basic usage:
```python
from speech_to_text import SpeechToText

converter = SpeechToText()
converter.process_files()
```

2. Output structure:
```
transcripts/
├── audio1.txt
├── audio2.txt
└── audio3.txt
```

## Error Handling

- Invalid audio files are skipped
- API errors are logged
- Temporary files are cleaned automatically

## Future Features

- [ ] Batch processing optimization
- [ ] Real-time transcription support
- [ ] Custom vocabulary support
- [ ] Enhanced multilingual support
- [ ] Subtitle generation

---

# 语音转文字工具

一个支持多种引擎的语音转文字 Python 工具。

## 功能特性

- 支持多种语音识别引擎：
  - 本地处理 (pocketsphinx)
  - Google Cloud Speech-to-Text
  - OpenAI Whisper（离线模型）
- 支持多种音频格式
- 可配置的输出格式
- 详细的日志记录

## 环境要求

- Python 3.10+
- ffmpeg（系统依赖）
- 其他依赖见 requirements.txt

## 安装

1. 安装系统依赖：
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# 从 https://ffmpeg.org/download.html 下载并添加到系统路径
```

2. 安装 Python 依赖：
```bash
pip install -r requirements.txt
```

## 配置

1. 复制示例配置文件：
```bash
cp config.example.json config.json
```

2. 配置文件说明：
```json
{
    "input_directory": "./audio",      // 输入音频文件目录
    "output_directory": "./transcripts", // 输出文本文件目录
    "model_directory": "./models",      // Whisper 模型存储目录
    "api_settings": {
        "provider": "whisper",          // 选择识别引擎：local/whisper/google
        "credentials": {
            "whisper": {
                "model": "base",        // 模型大小：tiny/base/small/medium/large
                "language": "fr",       // 目标语言
                "update_model": false   // 是否更新模型
            }
        }
    },
    "file_types": [                    // 支持的音频格式
        ".wav",
        ".mp3",
        ".m4a",
        ".flac",
        ".ogg"
    ],
    "output_format": {
        "type": "txt",                 // 输出文件格式
        "timestamp": true              // 是否包含时间戳
    },
    "logging": {
        "level": "INFO",               // 日志级别
        "file": "speech_to_text.log"   // 日志文件
    }
}
```

### Whisper 模型说明
| 模型  | 大小  | 所需内存 | 相对速度 | 适用场景 |
|-------|-------|----------|-----------|----------|
| tiny  | 39M   | ~1GB     | ~32x      | 快速测试 |
| base  | 74M   | ~1GB     | ~16x      | 简单场景 |
| small | 244M  | ~2GB     | ~6x       | 一般场景 |
| medium| 769M  | ~5GB     | ~2x       | 较高要求 |
| large | 1550M | ~10GB    | 1x        | 最高质量 |

## 安全注意事项

1. 配置文件安全：
   - 不要将包含凭证的配置文件提交到版本控制
   - 建议将 config.json 添加到 .gitignore

2. 模型文件管理：
   - 模型文件保存在 model_directory 指定目录
   - 首次运行时会自动下载模型
   - 模型文件可重复使用，无需重复下载

## 使用方法

1. 基本用法：
```python
from speech_to_text import SpeechToText

converter = SpeechToText()
converter.process_files()
```

2. 输出结构：
```
transcripts/
├── audio1.txt
├── audio2.txt
└── audio3.txt
```

## 错误处理

- 跳过无效的音频文件
- 记录 API 错误
- 自动清理临时文件

## 未来功能

- [ ] 批量处理优化
- [ ] 实时转写支持
- [ ] 自定义词汇支持
- [ ] 多语言支持增强
- [ ] 字幕生成功能 