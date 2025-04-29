import * as fs from 'fs';
import * as path from 'path';
import { format } from 'date-fns';
import { WechatSummarizerConfig } from '../config/config';

// 日志级别
export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error'
}

// 日志级别映射到数字
const LOG_LEVEL_PRIORITY: Record<LogLevel, number> = {
  [LogLevel.DEBUG]: 0,
  [LogLevel.INFO]: 1,
  [LogLevel.WARN]: 2,
  [LogLevel.ERROR]: 3
};

// 阶段日志类型
export enum StageLogType {
  START = 'START',
  PROGRESS = 'PROGRESS',
  SUCCESS = 'SUCCESS',
  FAILURE = 'FAILURE',
  WARNING = 'WARNING',
  COMPLETE = 'COMPLETE'
}

export class Logger {
  private config: WechatSummarizerConfig;
  private logFilePath: string;
  private detailedLogBasePath: string;
  private mainStream: fs.WriteStream | null = null;
  private detailedStreams: Map<string, fs.WriteStream> = new Map();
  private currentLevel: LogLevel;
  
  constructor(config: WechatSummarizerConfig) {
    this.config = config;
    this.currentLevel = config.logging.level as LogLevel || LogLevel.INFO;
    
    // 创建日志目录
    const logDir = path.join(config.storage.basePath, config.storage.logsDir);
    this.detailedLogBasePath = path.join(config.storage.basePath, config.storage.detailedLogsDir);
    
    fs.mkdirSync(logDir, { recursive: true });
    fs.mkdirSync(this.detailedLogBasePath, { recursive: true });
    
    // 设置主日志文件路径
    this.logFilePath = path.join(logDir, `${format(new Date(), 'yyyy-MM-dd')}.log`);
    
    // 打开主日志流
    if (config.logging.fileOutput) {
      this.mainStream = fs.createWriteStream(this.logFilePath, { flags: 'a' });
    }
    
    // 记录启动日志
    this.info('日志系统初始化完成');
    this.stage('SYSTEM', StageLogType.START, '微信聊天记录总结工具启动');
  }
  
  // 记录调试日志
  public debug(message: string): void {
    this.log(LogLevel.DEBUG, message);
  }
  
  // 记录信息日志
  public info(message: string): void {
    this.log(LogLevel.INFO, message);
  }
  
  // 记录警告日志
  public warn(message: string): void {
    this.log(LogLevel.WARN, message);
  }
  
  // 记录错误日志
  public error(message: string, error?: any): void {
    let logMessage = message;
    if (error) {
      if (error instanceof Error) {
        logMessage += ` - ${error.message}\n${error.stack}`;
      } else {
        logMessage += ` - ${JSON.stringify(error)}`;
      }
    }
    this.log(LogLevel.ERROR, logMessage);
  }
  
  // 记录阶段日志
  public stage(module: string, type: StageLogType, message: string, details?: any): void {
    // 检查是否启用了阶段日志
    if (!this.config.logging.stageLogging) return;
    
    // 构建详细信息
    let detailsStr = '';
    if (details) {
      detailsStr = typeof details === 'string' ? details : JSON.stringify(details, null, 2);
    }
    
    // 记录到主日志
    this.info(`[${module}][${type}] ${message}`);
    
    // 记录到详细日志
    if (this.config.logging.detailed) {
      const timestamp = format(new Date(), 'yyyy-MM-dd HH:mm:ss.SSS');
      const stageLog = `[${timestamp}][${type}] ${message}\n${detailsStr ? detailsStr + '\n' : ''}`;
      
      this.writeToDetailedLog(module, stageLog);
    }
  }
  
  // 写入到详细日志文件
  private writeToDetailedLog(module: string, content: string): void {
    try {
      // 确保模块目录存在
      const moduleDir = path.join(this.detailedLogBasePath, module);
      fs.mkdirSync(moduleDir, { recursive: true });
      
      // 获取或创建流
      const date = format(new Date(), 'yyyy-MM-dd');
      const logFilePath = path.join(moduleDir, `${date}.log`);
      
      let stream = this.detailedStreams.get(module);
      if (!stream) {
        stream = fs.createWriteStream(logFilePath, { flags: 'a' });
        this.detailedStreams.set(module, stream);
      }
      
      // 写入内容
      stream.write(content + '\n');
    } catch (error) {
      // 记录到主日志中
      this.error(`无法写入详细日志 ${module}`, error);
    }
  }
  
  // 记录器基础方法
  private log(level: LogLevel, message: string): void {
    // 检查日志级别
    if (LOG_LEVEL_PRIORITY[level] < LOG_LEVEL_PRIORITY[this.currentLevel]) {
      return;
    }
    
    const timestamp = format(new Date(), 'yyyy-MM-dd HH:mm:ss');
    const logEntry = `[${timestamp}][${level.toUpperCase()}] ${message}`;
    
    // 输出到控制台
    if (this.config.logging.consoleOutput) {
      switch (level) {
        case LogLevel.ERROR:
          console.error(logEntry);
          break;
        case LogLevel.WARN:
          console.warn(logEntry);
          break;
        case LogLevel.INFO:
          console.info(logEntry);
          break;
        case LogLevel.DEBUG:
          console.debug(logEntry);
          break;
      }
    }
    
    // 记录到文件
    if (this.config.logging.fileOutput && this.mainStream) {
      this.mainStream.write(logEntry + '\n');
    }
  }
  
  // 记录消息日志（专用于消息记录）
  public logMessage(groupName: string, message: any): void {
    if (!this.config.modules.mcpClient.logMessageContent) return;
    
    const sanitizedGroupName = groupName.replace(/[\\/:*?"<>|]/g, '_');
    const timestamp = format(new Date(), 'yyyy-MM-dd HH:mm:ss');
    const sender = message.from || 'unknown';
    const content = message.content || '';
    
    const logEntry = `[${timestamp}] ${sender}: ${content}`;
    
    // 写入到特定群的消息日志
    this.writeToDetailedLog(`messages/${sanitizedGroupName}`, logEntry);
  }
  
  // 记录样例消息（用于证明MCP连接正常）
  public logSampleMessages(groupName: string, messages: any[]): void {
    if (!this.config.modules.mcpClient.showSampleMessages) return;
    
    const sampleCount = Math.min(this.config.modules.mcpClient.sampleMessageCount, messages.length);
    const samples = messages.slice(0, sampleCount);
    
    let sampleText = `===== 群 "${groupName}" 的消息样例 (${sampleCount}/${messages.length}) =====\n`;
    
    samples.forEach((msg, idx) => {
      const time = format(new Date(msg.timestamp), 'MM-dd HH:mm:ss');
      sampleText += `${idx + 1}. [${time}] ${msg.from}: ${msg.content.substring(0, 50)}${msg.content.length > 50 ? '...' : ''}\n`;
    });
    
    sampleText += '===========================================\n';
    
    // 记录到主日志
    this.info(sampleText);
    
    // 记录到详细日志
    this.writeToDetailedLog('MCP_SAMPLES', `${format(new Date(), 'yyyy-MM-dd HH:mm:ss')} - ${groupName}\n${sampleText}`);
  }
  
  // 关闭日志
  public close(): void {
    // 关闭主日志流
    if (this.mainStream) {
      this.mainStream.end();
      this.mainStream = null;
    }
    
    // 关闭所有详细日志流
    for (const [module, stream] of this.detailedStreams.entries()) {
      stream.end();
    }
    this.detailedStreams.clear();
    
    console.log('日志系统已关闭');
  }
} 