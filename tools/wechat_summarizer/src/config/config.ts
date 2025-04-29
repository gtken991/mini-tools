import { readFileSync } from 'fs';
import { resolve } from 'path';
import * as yaml from 'js-yaml';

export interface WechatSummarizerConfig {
  // 基本配置
  storage: {
    basePath: string;           // 导出和存储的基础路径
    messageDir: string;         // 消息存储子目录
    summaryDir: string;         // 总结存储子目录
    logsDir: string;            // 日志存储子目录
    detailedLogsDir: string;    // 详细日志子目录
    exportFormats: string[];    // 支持的导出格式 ['json', 'txt', 'md']
  };
  
  // 功能模块配置
  modules: {
    messageRecording: {
      enabled: boolean;         // 是否启用消息记录功能
      saveRawMessage: boolean;  // 是否保存原始消息格式
    };
    mcpClient: {
      enabled: boolean;         // 是否启用MCP客户端
      autoReconnect: boolean;   // 断开连接后是否自动重连
      maxReconnectAttempts: number; // 最大重连次数
      logMessageContent: boolean; // 是否记录消息内容
      monitoringActive: boolean; // 是否监控活跃状态
      showSampleMessages: boolean; // 是否显示样例消息(用于验证连接)
      sampleMessageCount: number; // 显示的样例消息数量
    };
    aiSummary: {
      enabled: boolean;         // 是否启用AI总结
      cursorApiKey: string;     // Cursor API密钥
      cursorApiUrl: string;     // Cursor API URL
      summaryInterval: number;  // 总结间隔(分钟)
      summaryPrompt: string;    // 总结提示词模板
      maxMessagesPerSummary: number; // 每次总结最大消息数
    };
  };
  
  // 日志配置
  logging: {
    level: string;              // 日志等级: 'debug' | 'info' | 'warn' | 'error'
    detailed: boolean;          // 是否开启详细日志
    stageLogging: boolean;      // 是否记录阶段状态
    consoleOutput: boolean;     // 是否输出到控制台
    fileOutput: boolean;        // 是否输出到文件
  };
  
  // 微信MCP相关配置
  wechat: {
    mcpWsPort: number;          // MCP WebSocket端口
    mcpApiHost: string;         // MCP API主机地址
    groupNames: string[];       // 要监听的群名列表
    historyMsgCount: number;    // 初始化时获取的历史消息数量
  };
  
  // 关键词监控配置
  keywords: {
    enabled: boolean;           // 是否启用关键词监控
    words: string[];            // 关键词列表
    notificationEnabled: boolean; // 是否启用关键词通知
    highlightInSummary: boolean;  // 在总结中高亮关键词
  };
}

// 默认配置
const defaultConfig: WechatSummarizerConfig = {
  storage: {
    basePath: './data',
    messageDir: 'messages',
    summaryDir: 'summaries',
    logsDir: 'logs',
    detailedLogsDir: 'detailed_logs',
    exportFormats: ['json', 'txt', 'md']
  },
  modules: {
    messageRecording: {
      enabled: true,
      saveRawMessage: true
    },
    mcpClient: {
      enabled: true,
      autoReconnect: true,
      maxReconnectAttempts: 10,
      logMessageContent: false,
      monitoringActive: true,
      showSampleMessages: true,
      sampleMessageCount: 5
    },
    aiSummary: {
      enabled: true,
      cursorApiKey: '',
      cursorApiUrl: 'https://api.cursor.sh/v1/chat/completions',
      summaryInterval: 60,
      summaryPrompt: '请总结以下微信群聊消息，重点提取有价值的信息和讨论要点：\n\n{{messages}}\n\n',
      maxMessagesPerSummary: 200
    }
  },
  logging: {
    level: 'info',
    detailed: true,
    stageLogging: true,
    consoleOutput: true,
    fileOutput: true
  },
  wechat: {
    mcpWsPort: 19099,
    mcpApiHost: 'http://localhost:19088',
    groupNames: [],
    historyMsgCount: 100
  },
  keywords: {
    enabled: true,
    words: ['重要', '紧急', '会议', '截止日期'],
    notificationEnabled: true,
    highlightInSummary: true
  }
};

// 加载配置
export function loadConfig(configPath: string = './config.yaml'): WechatSummarizerConfig {
  try {
    const configFile = readFileSync(resolve(process.cwd(), configPath), 'utf8');
    const userConfig = yaml.load(configFile) as Partial<WechatSummarizerConfig>;
    
    // 深度合并配置
    return mergeConfigs(defaultConfig, userConfig);
  } catch (error) {
    console.warn(`配置文件加载失败，使用默认配置: ${error}`);
    return defaultConfig;
  }
}

// 深度合并配置
function mergeConfigs(defaultConfig: WechatSummarizerConfig, userConfig: Partial<WechatSummarizerConfig>): WechatSummarizerConfig {
  // 创建克隆的对象
  const result: WechatSummarizerConfig = JSON.parse(JSON.stringify(defaultConfig));
  
  if (!userConfig) return result;
  
  // 处理 storage 属性
  if (userConfig.storage) {
    Object.assign(result.storage, userConfig.storage);
  }
  
  // 处理 modules 属性及其嵌套属性
  if (userConfig.modules) {
    if (userConfig.modules.messageRecording) {
      Object.assign(result.modules.messageRecording, userConfig.modules.messageRecording);
    }
    if (userConfig.modules.mcpClient) {
      Object.assign(result.modules.mcpClient, userConfig.modules.mcpClient);
    }
    if (userConfig.modules.aiSummary) {
      Object.assign(result.modules.aiSummary, userConfig.modules.aiSummary);
    }
  }
  
  // 处理 logging 属性
  if (userConfig.logging) {
    Object.assign(result.logging, userConfig.logging);
  }
  
  // 处理 wechat 属性
  if (userConfig.wechat) {
    Object.assign(result.wechat, userConfig.wechat);
  }
  
  // 处理 keywords 属性
  if (userConfig.keywords) {
    Object.assign(result.keywords, userConfig.keywords);
  }
  
  return result;
} 