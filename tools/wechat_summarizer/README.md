# 微信聊天记录总结工具

一个用于自动获取微信群聊消息并使用 AI 进行智能总结的工具。基于微信PC客户端(MCP)接口，可靠且稳定。

## 功能特点

- 通过MCP接口自动获取指定微信群的聊天记录
- 支持多个群聊同时监控
- 按日期和群组分类存储聊天记录
- 支持按时间范围查询消息
- 使用 Cursor API 进行智能总结
- 支持关键词检测和提醒
- 可配置的总结间隔和导出格式
- 支持导出多种格式（JSON、TXT、Markdown）
- 完全可配置化的系统

## 技术栈

- TypeScript
- Node.js
- MCP (微信PC客户端接口)
- Cursor API (AI 总结)

## 安装

1. 确保已安装[微信MCP工具](https://github.com/tom-snow/wechat-windows-versions)并配置好

2. 克隆项目并进入目录：
```bash
cd tools/wechat_summarizer
```

3. 安装依赖：
```bash
npm install
```

4. 配置：
   - 复制 `config.yaml.example` 为 `config.yaml`
   - 根据需要修改配置文件中的参数

## 使用方法

1. 构建项目：
```bash
npm run build
```

2. 启动服务：
```bash
npm run start
```

或开发模式：
```bash
npm run dev
```

3. 程序会自动：
   - 连接微信MCP服务并监听指定群组的消息
   - 保存消息到本地文件（按群名和日期分类）
   - 根据配置的时间间隔生成消息总结
   - 在检测到关键词时触发通知

## 配置说明

所有配置选项都存储在 `config.yaml` 文件中，支持的主要配置包括：

### 存储配置
```yaml
storage:
  basePath: "./data"                 # 数据存储的基础路径
  messageDir: "messages"             # 消息存储目录
  summaryDir: "summaries"            # 总结存储目录
  exportFormats: ["json", "txt", "md"] # 支持的导出格式
```

### 微信MCP配置
```yaml
wechat:
  mcpWsPort: 19099                  # MCP WebSocket端口
  mcpApiHost: "http://localhost:19088" # MCP API主机地址
  groupNames:                       # 要监听的群名列表
    - "项目讨论组"
    - "技术交流群"
  historyMsgCount: 100              # 初始化时获取的历史消息数量
```

### AI总结配置
```yaml
summary:
  enabled: true                     # 是否启用AI总结
  cursorApiKey: "your-cursor-api-key" # Cursor API密钥
  summaryInterval: 60               # 总结间隔(分钟)
  summaryPrompt: "请总结以下微信群聊消息..." # 总结提示词模板
```

### 关键词监控配置
```yaml
keywords:
  enabled: true                    # 是否启用关键词监控
  words:                           # 关键词列表
    - "重要"
    - "紧急"
  notificationEnabled: true        # 是否启用关键词通知
```

## 数据结构

- `/data/messages/{群名}/{日期}.json` - 存储原始消息
- `/data/summaries/{群名}/{日期}.json` - 存储生成的总结
- `/data/summaries/{群名}/{日期}.md` - Markdown格式的总结
- `/data/logs/{日期}.log` - 日志文件

## 依赖项

- [Cursor API](https://cursor.sh) - 用于生成AI总结
- [微信MCP工具](https://github.com/tom-snow/wechat-windows-versions) - 用于获取微信消息

## 注意事项

1. 使用前请确保微信MCP工具已正确配置并运行
2. 确保有足够的存储空间保存消息历史
3. 请遵守相关平台的使用条款和规定

## 开发计划

- [ ] 添加Web界面，可视化展示总结结果
- [ ] 支持更多AI模型和API
- [ ] 添加消息导出到第三方平台功能
- [ ] 添加用户交互功能，如指令触发和查询

## 许可证

MIT License 