import WebSocket from 'ws';
import axios from 'axios';
import { ChatMessage } from '../types';
import { WechatSummarizerConfig } from '../config/config';
import * as fs from 'fs';
import * as path from 'path';
import { format } from 'date-fns';
import { EventEmitter } from 'events';
import { Logger, StageLogType } from './logger';

// 定义MCP消息类型
interface MCPMessage {
  id: string;
  type: string;
  wxid: string;
  roomid?: string;
  sender?: string;
  content: string;
  timestamp: number;
}

export class WeChatMCPService extends EventEmitter {
  private config: WechatSummarizerConfig;
  private logger: Logger;
  private ws: WebSocket | null = null;
  private connected = false;
  private apiHost: string;
  private reconnectAttempts = 0;
  private messageStoragePath: string;
  private isRecordingEnabled: boolean;

  constructor(config: WechatSummarizerConfig, logger: Logger) {
    super();
    this.config = config;
    this.logger = logger;
    this.apiHost = config.wechat.mcpApiHost;
    this.messageStoragePath = path.join(
      config.storage.basePath,
      config.storage.messageDir
    );
    
    this.isRecordingEnabled = config.modules.messageRecording.enabled;
    
    // 确保存储目录存在
    if (this.isRecordingEnabled) {
      this.ensureStorageDirectories();
    }
  }

  private ensureStorageDirectories(): void {
    // 确保消息目录存在
    fs.mkdirSync(this.messageStoragePath, { recursive: true });
    this.logger.stage('STORAGE', StageLogType.SUCCESS, '消息存储目录创建成功', {
      path: this.messageStoragePath
    });
  }

  public async start(): Promise<void> {
    // 检查是否启用MCP客户端
    if (!this.config.modules.mcpClient.enabled) {
      this.logger.warn('MCP客户端模块已禁用，跳过启动');
      return;
    }
    
    this.logger.stage('MCP', StageLogType.START, 'MCP客户端服务启动中');
    
    try {
      // 连接到MCP WebSocket
      await this.connectWebSocket();
      
      // 获取历史消息
      if (this.isRecordingEnabled) {
        for (const groupName of this.config.wechat.groupNames) {
          try {
            this.logger.info(`开始获取群 ${groupName} 的历史消息`);
            const roomId = await this.getRoomIdByName(groupName);
            if (roomId) {
              await this.fetchHistoryMessages(roomId, this.config.wechat.historyMsgCount);
            } else {
              this.logger.warn(`无法找到群 ${groupName} 的ID`);
            }
          } catch (error) {
            this.logger.error(`获取群 ${groupName} 的历史消息失败`, error);
          }
        }
      } else {
        this.logger.info('消息记录功能已禁用，跳过历史消息获取');
      }
      
      this.logger.stage('MCP', StageLogType.SUCCESS, 'MCP客户端服务启动成功');
    } catch (error) {
      this.logger.stage('MCP', StageLogType.FAILURE, 'MCP客户端服务启动失败', error);
      throw error;
    }
  }

  private async connectWebSocket(): Promise<void> {
    try {
      const wsUrl = `ws://localhost:${this.config.wechat.mcpWsPort}`;
      this.logger.info(`正在连接到MCP WebSocket: ${wsUrl}`);
      
      this.ws = new WebSocket(wsUrl);
      
      this.ws.on('open', () => {
        this.logger.stage('MCP', StageLogType.SUCCESS, '已连接到微信MCP WebSocket服务');
        this.connected = true;
        this.reconnectAttempts = 0;
      });
      
      this.ws.on('message', (data: string) => {
        try {
          const message = JSON.parse(data);
          this.handleMessage(message);
        } catch (error) {
          this.logger.error('解析WebSocket消息失败', error);
        }
      });
      
      this.ws.on('close', () => {
        this.logger.stage('MCP', StageLogType.WARNING, 'WebSocket连接已关闭');
        this.connected = false;
        
        if (this.config.modules.mcpClient.autoReconnect) {
          this.attemptReconnect();
        }
      });
      
      this.ws.on('error', (error) => {
        this.logger.error('WebSocket连接错误', error);
        this.connected = false;
        
        if (this.config.modules.mcpClient.autoReconnect) {
          this.attemptReconnect();
        }
      });
    } catch (error) {
      this.logger.error('连接到WebSocket服务失败', error);
      if (this.config.modules.mcpClient.autoReconnect) {
        this.attemptReconnect();
      } else {
        throw error;
      }
    }
  }

  private attemptReconnect(): void {
    const maxReconnectAttempts = this.config.modules.mcpClient.maxReconnectAttempts;
    
    if (this.reconnectAttempts < maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts - 1), 30000);
      this.logger.info(`尝试在 ${delay / 1000} 秒后重新连接... (${this.reconnectAttempts}/${maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connectWebSocket().catch(error => {
          this.logger.error('重新连接失败', error);
        });
      }, delay);
    } else {
      this.logger.stage('MCP', StageLogType.FAILURE, '重连次数超过最大限制，无法重新连接');
    }
  }

  private async handleMessage(message: MCPMessage): Promise<void> {
    // 只处理群消息
    if (message.type === 'group_message' && message.roomid) {
      // 检查是否是我们需要监听的群
      const roomName = await this.getRoomNameById(message.roomid);
      if (this.config.wechat.groupNames.includes(roomName)) {
        const formattedMessage = {
          id: message.id,
          from: message.sender || message.wxid,
          roomId: message.roomid,
          roomName,
          content: message.content,
          timestamp: message.timestamp,
          type: message.type
        };
        
        // 记录消息内容到日志
        this.logger.logMessage(roomName, formattedMessage);
        
        // 保存消息到文件
        if (this.isRecordingEnabled) {
          await this.saveMessage(formattedMessage);
        }
        
        // 发出事件通知
        this.emit('message', formattedMessage);
        
        // 检查关键词
        if (this.config.keywords.enabled) {
          this.checkKeywords(formattedMessage);
        }
      }
    }
  }

  private async saveMessage(message: any): Promise<void> {
    if (!this.isRecordingEnabled) return;
    
    try {
      const date = format(new Date(message.timestamp), 'yyyy-MM-dd');
      const groupFolder = path.join(this.messageStoragePath, message.roomName.replace(/[\\/:*?"<>|]/g, '_'));
      
      // 确保群聊目录存在
      fs.mkdirSync(groupFolder, { recursive: true });
      
      const filePath = path.join(groupFolder, `${date}.json`);
      
      const chatMessage: ChatMessage = {
        id: message.id,
        from: message.from,
        roomId: message.roomId,
        roomName: message.roomName,
        content: message.content,
        timestamp: message.timestamp,
        type: message.type
      };
  
      // 读取已有消息或创建新的数组
      let messages: ChatMessage[] = [];
      try {
        if (fs.existsSync(filePath)) {
          const content = await fs.promises.readFile(filePath, 'utf-8');
          messages = JSON.parse(content);
        }
      } catch (error) {
        this.logger.error(`读取消息文件 ${filePath} 失败`, error);
        // 出错时创建新数组
        messages = [];
      }
  
      // 添加新消息并保存
      messages.push(chatMessage);
      await fs.promises.writeFile(filePath, JSON.stringify(messages, null, 2));
      
      // 记录到详细日志
      if (messages.length % 10 === 0) { // 每10条消息记录一次，避免日志过多
        this.logger.stage('MESSAGE', StageLogType.PROGRESS, `已保存 ${messages.length} 条消息到 ${message.roomName}`);
      }
    } catch (error) {
      this.logger.error('保存消息失败', error);
    }
  }

  private checkKeywords(message: ChatMessage): void {
    const { content } = message;
    const matchedKeywords = this.config.keywords.words.filter(keyword => 
      content.includes(keyword)
    );
    
    if (matchedKeywords.length > 0) {
      this.emit('keyword_matched', {
        message,
        keywords: matchedKeywords
      });
      
      if (this.config.keywords.notificationEnabled) {
        this.logger.stage('KEYWORD', StageLogType.PROGRESS, `关键词匹配`, {
          group: message.roomName,
          sender: message.from,
          keywords: matchedKeywords,
          message: content.substring(0, 50) + (content.length > 50 ? '...' : '')
        });
      }
    }
  }

  public async getMessagesByDate(roomName: string, date: string): Promise<ChatMessage[]> {
    // 检查是否启用了消息记录
    if (!this.isRecordingEnabled) {
      this.logger.warn(`消息记录功能已禁用，无法获取消息`);
      return [];
    }
    
    const groupFolder = path.join(this.messageStoragePath, roomName.replace(/[\\/:*?"<>|]/g, '_'));
    const filePath = path.join(groupFolder, `${date}.json`);
    
    if (!fs.existsSync(filePath)) {
      this.logger.debug(`消息文件不存在: ${filePath}`);
      return [];
    }

    try {
      const content = await fs.promises.readFile(filePath, 'utf-8');
      const messages = JSON.parse(content) as ChatMessage[];
      
      // 当开启了"仅展示样例消息"且未启用AI总结功能时，记录样例消息到日志
      if (this.config.modules.mcpClient.showSampleMessages && !this.config.modules.aiSummary.enabled) {
        this.logger.logSampleMessages(roomName, messages);
      }
      
      return messages;
    } catch (error) {
      this.logger.error(`读取消息文件 ${filePath} 失败`, error);
      return [];
    }
  }
  
  public async getMessagesByDateRange(roomName: string, startDate: string, endDate: string): Promise<ChatMessage[]> {
    // 检查是否启用了消息记录
    if (!this.isRecordingEnabled) {
      this.logger.warn(`消息记录功能已禁用，无法获取消息`);
      return [];
    }
    
    this.logger.debug(`获取 ${roomName} 从 ${startDate} 到 ${endDate} 的消息`);
    
    // 解析开始和结束日期
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    let allMessages: ChatMessage[] = [];
    const currentDate = new Date(start);
    
    // 遍历日期范围
    while (currentDate <= end) {
      const dateStr = format(currentDate, 'yyyy-MM-dd');
      const messages = await this.getMessagesByDate(roomName, dateStr);
      allMessages = [...allMessages, ...messages];
      
      // 增加一天
      currentDate.setDate(currentDate.getDate() + 1);
    }
    
    this.logger.debug(`获取到 ${allMessages.length} 条消息`);
    return allMessages;
  }

  private async getRoomIdByName(roomName: string): Promise<string | null> {
    try {
      this.logger.debug(`尝试获取群 ${roomName} 的ID`);
      const response = await axios.get(`${this.apiHost}/api/group/list`);
      const groups = response.data.data || [];
      
      const group = groups.find((g: any) => g.name === roomName);
      
      if (group) {
        this.logger.debug(`群 ${roomName} 的ID为 ${group.id}`);
        return group.id;
      } else {
        this.logger.warn(`找不到群 ${roomName}`);
        return null;
      }
    } catch (error) {
      this.logger.error(`获取群ID失败`, error);
      return null;
    }
  }
  
  private async getRoomNameById(roomId: string): Promise<string> {
    try {
      const response = await axios.get(`${this.apiHost}/api/group/info?id=${roomId}`);
      const roomName = response.data.data?.name || roomId;
      return roomName;
    } catch (error) {
      this.logger.error(`获取群名称失败`, error);
      return roomId;
    }
  }

  private async fetchHistoryMessages(roomId: string, count: number): Promise<void> {
    if (!this.isRecordingEnabled) {
      return;
    }
    
    try {
      this.logger.stage('MCP', StageLogType.PROGRESS, `获取群 ${roomId} 的历史消息`);
      
      const response = await axios.get(
        `${this.apiHost}/api/message/history?roomid=${roomId}&count=${count}`
      );
      
      const messages = response.data.data || [];
      const roomName = await this.getRoomNameById(roomId);
      
      // 保存历史消息
      this.logger.info(`开始保存 ${messages.length} 条历史消息`);
      
      for (const msg of messages) {
        await this.saveMessage({
          id: msg.id,
          from: msg.sender || msg.wxid,
          roomId,
          roomName,
          content: msg.content,
          timestamp: msg.timestamp,
          type: 'group_message'
        });
      }
      
      this.logger.stage('MCP', StageLogType.SUCCESS, `成功获取并保存群 ${roomName} 的 ${messages.length} 条历史消息`);
      
      // 记录样例消息
      if (this.config.modules.mcpClient.showSampleMessages) {
        this.logger.logSampleMessages(roomName, messages.slice(0, this.config.modules.mcpClient.sampleMessageCount));
      }
    } catch (error) {
      this.logger.stage('MCP', StageLogType.FAILURE, `获取历史消息失败`, error);
    }
  }

  public isEnabled(): boolean {
    return this.config.modules.mcpClient.enabled;
  }
  
  public isConnected(): boolean {
    return this.connected;
  }

  public async stop(): Promise<void> {
    if (this.ws) {
      this.logger.stage('MCP', StageLogType.PROGRESS, 'MCP客户端服务正在关闭');
      this.ws.close();
      this.logger.stage('MCP', StageLogType.COMPLETE, 'MCP客户端服务已关闭');
    }
  }
} 