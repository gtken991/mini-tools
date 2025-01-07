# Tarot Reader 塔罗牌阅读器

一个现代化的塔罗牌阅读器应用，提供直观的界面和智能的解读系统。基于 React + FastAPI 构建，支持多种牌阵布局和详细的牌义解读。

## 功能特性

### 前端特性
- 🎴 优雅的卡牌展示界面
- 🌓 支持明暗主题切换
- 📱 完全响应式设计
- 🔄 流畅的卡牌翻转动画
- 🖼️ 精美的塔罗牌图片
- 🔍 详细的牌义解读
- ⚡️ 快速的页面加载和响应

### 后端特性
- 🎯 RESTful API 设计
- 🔮 智能的塔罗牌解读系统
- 🎴 支持多种牌阵布局
  - 单张牌阵
  - 三张牌阵（过去-现在-未来）
  - 凯尔特十字牌阵
- 🖼️ 自动下载和处理塔罗牌图片
- 🔒 安全的 CORS 配置
- 📝 完善的日志系统

## 开发环境要求

### 前端要求
- Node.js >= 16
- npm >= 8

### 后端要求
- Python >= 3.8
- pip

## 项目结构
```
tarot_reader/
├── frontend/           # React 前端项目
│   ├── src/           # 源代码
│   │   ├── api/       # API 接口
│   │   ├── components/# React 组件
│   │   ├── hooks/     # 自定义 Hooks
│   │   └── styles/    # 样式文件
│   └── public/        # 静态资源
├── tarot_reader/      # Python 后端项目
│   ├── run_app.py     # 应用入口
│   ├── tarot_service.py # 核心服务
│   └── scripts/       # 工具脚本
│       └── download_images.py  # 图片下载工具
└── tests/             # 测试文件
```

## 环境配置
1. 复制环境变量示例文件：
```bash
# 后端配置
cp .env.example .env
# 前端配置
cd frontend && cp .env.example .env
```

2. 修改环境变量：

### 后端环境变量
- `ALLOWED_ORIGINS`: 允许的跨域来源
- `LOG_LEVEL`: 日志级别（INFO/WARNING/ERROR）
- `UNSPLASH_ACCESS_KEY`: Unsplash API 密钥（用于下载图片）

### 前端环境变量
- `VITE_API_BASE_URL`: API 服务器地址
- `NODE_ENV`: 运行环境（development/production）

## API 端点

- `POST /api/reading`
  - 参数：
    - `question`: 用户的问题
    - `spread_type`: 牌阵类型（single_card/three_card/celtic_cross）
  - 返回：塔罗牌解读结果

## 安装
```bash
# 安装后端依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
```

3. 启动服务：
```bash
# 启动后端服务
python -m tarot_reader.run_app

# 启动前端开发服务器
cd frontend
npm run dev
```

## API 端点

### 塔罗牌解读
- `POST /api/reading`
  - 参数：
    - `question`: 用户的问题
    - `spread_type`: 牌阵类型（single_card/three_card/celtic_cross）
  - 返回：
    - `cards`: 抽取的卡牌信息
    - `result`: 详细的解读结果


## 工作原理

1. 图片管理
   - 使用 Unsplash API 下载高质量图片
   - 自动处理图片尺寸和格式
   - 本地缓存优化加载速度

2. 牌阵布局
   - 根据问题类型选择合适的牌阵
   - 考虑卡牌的位置和关系
   - 生成直观的可视化展示

3. 解读系统
   - 分析卡牌组合含义
   - 结合问题背景
   - 生成详细的解读报告

## 注意事项

1. API 使用
   - 需要设置 Unsplash API Key
   - 注意 API 调用频率限制
   - 确保环境变量配置正确

2. 安全提示
   - 保护好你的 API 密钥
   - 在生产环境中使用安全的 CORS 配置
   - 使用适当的日志级别

## 常见问题

1. 图片无法加载？
   - 检查 Unsplash API Key 是否正确
   - 确认网络连接正常
   - 查看浏览器控制台错误信息

2. 解读结果不准确？
   - 确保问题描述清晰
   - 选择合适的牌阵类型
   - 考虑使用更详细的牌阵

## 更新日志

- 2024.01.05: 添加凯尔特十字牌阵支持
- 2024.01.05: 优化图片加载性能
- 2024.01.05: 改进解读算法

## 许可证
MIT 