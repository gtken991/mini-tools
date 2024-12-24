# Bilibili 字幕下载工具

这是一个用于下载哔哩哔哩视频字幕的Python工具。支持下载视频的CC字幕并转换为SRT格式。

## 功能特性

- 支持长短链接解析
- 支持异步并发下载
- 自动转换为SRT格式
- 支持分P视频字幕下载
- 内置请求重试机制
- 完善的错误处理

## 环境要求

- Python 3.10+
- pip 21.2.4+

## 安装依赖
pip install requests>=2.31.0

pip install aiohttp>=3.9.1

pip install aiohttp-retry>=2.8.3

pip install tenacity>=8.2.3

pip install typing-extensions>=4.7.1

pip install python-dateutil>=2.8.2

pip install colorlog>=6.7.0


## 使用方法

1. 配置文件设置
   - 打开 `config.json`
   - 填入你的B站cookie（从浏览器开发者工具中获取）

2. 运行示例：
   - 运行 `python subtitle_bilibili.py`
   - 输入视频链接，选择下载字幕的语言
   - 等待下载完成，字幕文件将保存在 `BV*/` 目录下

3. 注意事项：
   - 请确保你的网络环境能够访问B站
   - 如果下载失败，请检查你的cookie是否正确
   - 如果需要下载多个视频，请多次运行程序

设置要下载的视频URL
urls = [
"https://b23.tv/xxxxx", # 短链接示例
"https://www.bilibili.com/video/xxxxx" # 长链接示例
]


直接运行脚本
python subtitle_bilibili.py


## 工作原理

1. 链接解析
   - 支持长链接和短链接自动识别
   - 自动提取视频BV号

2. 字幕下载
   - 异步并发下载提高效率
   - 自动处理多P视频
   - 内置请求重试机制

3. 格式转换
   - 自动将JSON格式转换为SRT
   - 保留原始JSON文件

## 输出结构

BV号文件夹/

    ├── P1.json # 原始JSON字幕

    ├── P2.json

    ├── srt/ # 转换后的SRT字幕

       ├── P1.srt

       └── P2.srt


- 每个视频的目录下，包含一个 `BV*.json` 文件，以及对应的 `BV*.srt` 文件
- 如果视频有多个P，则每个P的目录下，包含一个 `BV*.json` 文件，以及对应的 `BV*.srt` 文件
- 如果视频没有字幕，则不生成任何文件

## 异常处理

- 网络错误：自动重试
- 无字幕视频：跳过并记录日志
- Cookie失效：提示更新
- 请求限制：自动等待重试

## 注意事项

1. 使用限制
   - 仅支持CC字幕视频
   - 需要登录cookie
   - 注意请求频率限制

2. 安全提示
   - 不要分享你的cookie
   - 确保 `config.json` 已加入 `.gitignore`

## 常见问题

1. 如何获取Cookie？
   - 登录B站
   - 打开浏览器开发者工具(F12)
   - 在Network标签页找到cookie

2. 下载失败怎么办？
   - 检查cookie是否有效
   - 确认视频是否有CC字幕
   - 查看日志文件了解详细错误

3. 为什么要转换为SRT格式？
   - SRT是通用字幕格式
   - 支持大多数播放器
   - 便于编辑和使用

## 更新日志

- 2024.12.24: 添加异步下载支持
- 2024.12.24: 优化错误处理机制
- 2024.12.24: 添加详细日志记录
