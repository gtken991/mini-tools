# 微信聊天记录总结工具

一个用于自动获取微信群聊消息并使用 AI 进行智能总结的工具。

## 功能特点

- 自动获取指定微信群的聊天记录
- 按日期存储聊天记录
- 支持按时间范围查询消息
- 使用 AI 进行智能总结
- 支持关键词关注
- 支持自定义总结规则

## 技术栈

- TypeScript
- Node.js
- wechat4u (微信网页版 API)
- Cursor API (AI 总结)

## 安装

1. 克隆项目并进入目录：
```bash
cd tools/wechat_summarizer
```

2. 安装依赖：
```bash
npm install
```

3. 配置环境变量：
创建 `.env` 文件并配置以下内容：
```
WECHAT_STORAGE_PATH=./data/wechat
TARGET_GROUP_NAME=你的目标群名称
CURSOR_API_KEY=your_cursor_api_key
CURSOR_API_URL=https://api.cursor.sh/v1/chat/completions
```

## 使用方法

1. 启动服务：
```bash
npm run dev
```

2. 程序会自动：
   - 连接微信并监听指定群组的消息
   - 保存消息到本地文件
   - 定期生成消息总结

## 注意事项

1. 需要确保微信账号可以登录网页版微信
2. 需要有效的 Cursor API 密钥
3. 建议定期备份消息数据
4. 请遵守相关平台的使用条款和规定

## 配置说明

### 环境变量

- `WECHAT_STORAGE_PATH`: 消息存储路径
- `TARGET_GROUP_NAME`: 目标群组名称
- `CURSOR_API_KEY`: Cursor API 密钥
- `CURSOR_API_URL`: Cursor API 地址

### 自定义配置

可以在 `src/services/summary.ts` 中修改：
- 总结提示词
- 关键词过滤规则
- 总结格式

## 开发计划

- [ ] 支持多个群组同时监控
- [ ] 添加 Web 界面
- [ ] 支持更多 AI 模型
- [ ] 添加消息导出功能
- [ ] 支持自定义总结模板

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License 