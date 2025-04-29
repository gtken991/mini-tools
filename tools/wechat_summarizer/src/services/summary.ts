import axios from 'axios';
import { ChatMessage, SummaryConfig, SummaryResult } from '../types';
import { WechatSummarizerConfig } from '../config/config';
import { format, parseISO } from 'date-fns';
import * as fs from 'fs';
import * as path from 'path';
import { Logger, StageLogType } from './logger';

export class SummaryService {
  private config: WechatSummarizerConfig;
  private logger: Logger;
  private summaryStoragePath: string;
  private aiSummaryEnabled: boolean;

  constructor(config: WechatSummarizerConfig, logger: Logger) {
    this.config = config;
    this.logger = logger;
    this.aiSummaryEnabled = config.modules.aiSummary.enabled;
    this.summaryStoragePath = path.join(
      config.storage.basePath,
      config.storage.summaryDir
    );
    
    // 确保总结存储目录存在
    if (this.aiSummaryEnabled) {
      this.ensureStorageDirectory();
    } else {
      this.logger.info('AI总结功能已禁用');
    }
  }
  
  private ensureStorageDirectory(): void {
    fs.mkdirSync(this.summaryStoragePath, { recursive: true });
    this.logger.stage('STORAGE', StageLogType.SUCCESS, '总结存储目录创建成功', {
      path: this.summaryStoragePath
    });
  }

  public async summarize(messages: ChatMessage[], summaryConfig: SummaryConfig): Promise<SummaryResult> {
    // 检查是否启用了总结功能
    if (!this.aiSummaryEnabled && !summaryConfig.enableAI) {
      this.logger.warn('AI总结功能已禁用');
      return this.generateEmptySummary(summaryConfig, messages);
    }
    
    this.logger.stage('SUMMARY', StageLogType.START, `开始为群 ${summaryConfig.groupName} 生成总结`);
    
    // 获取配置
    const useAI = summaryConfig.enableAI !== undefined 
      ? summaryConfig.enableAI 
      : this.aiSummaryEnabled;
    
    const maxMessages = summaryConfig.maxMessages || this.config.modules.aiSummary.maxMessagesPerSummary;
    
    // 过滤消息
    const filteredMessages = this.filterMessages(messages, summaryConfig)
      .slice(-maxMessages); // 只取最新的N条消息
    
    if (filteredMessages.length === 0) {
      this.logger.warn(`没有找到符合条件的消息`);
      return this.generateEmptySummary(summaryConfig, messages);
    }
    
    // 计算关键词匹配
    const keywordMatches = this.countKeywordMatches(filteredMessages, summaryConfig.keywords || []);
    this.logger.debug(`找到 ${Object.keys(keywordMatches).length} 个关键词匹配`);
    
    // 生成总结
    let summary: string;
    if (useAI && this.config.modules.aiSummary.cursorApiKey) {
      this.logger.stage('SUMMARY', StageLogType.PROGRESS, `使用AI生成总结，消息数量: ${filteredMessages.length}`);
      summary = await this.generateAISummary(filteredMessages, summaryConfig.keywords || []);
    } else {
      this.logger.stage('SUMMARY', StageLogType.PROGRESS, `使用基本统计生成总结，消息数量: ${filteredMessages.length}`);
      summary = this.generateBasicSummary(filteredMessages, summaryConfig.keywords || []);
    }
    
    // 创建结果
    const result: SummaryResult = {
      summary,
      keywords: summaryConfig.keywords || [],
      dateRange: {
        start: summaryConfig.startDate || format(new Date(filteredMessages[0]?.timestamp) || new Date(), 'yyyy-MM-dd'),
        end: summaryConfig.endDate || format(new Date(filteredMessages[filteredMessages.length - 1]?.timestamp) || new Date(), 'yyyy-MM-dd')
      },
      groupName: summaryConfig.groupName,
      messageCount: filteredMessages.length,
      keywordMatches
    };
    
    // 保存总结
    if (summaryConfig.outputFormat || this.config.storage.exportFormats.length > 0) {
      await this.saveSummary(result, summaryConfig);
    }
    
    this.logger.stage('SUMMARY', StageLogType.SUCCESS, `总结生成成功，长度: ${summary.length}字符`);
    return result;
  }

  private generateEmptySummary(config: SummaryConfig, messages: ChatMessage[]): SummaryResult {
    return {
      summary: "没有找到符合条件的消息或AI总结功能已禁用",
      keywords: config.keywords || [],
      dateRange: {
        start: config.startDate || format(new Date(), 'yyyy-MM-dd'),
        end: config.endDate || format(new Date(), 'yyyy-MM-dd')
      },
      groupName: config.groupName,
      messageCount: messages.length,
      keywordMatches: {}
    };
  }

  private filterMessages(messages: ChatMessage[], config: SummaryConfig): ChatMessage[] {
    this.logger.debug(`过滤消息，原始消息数量: ${messages.length}`);
    
    const filtered = messages.filter(msg => {
      const msgDate = format(new Date(msg.timestamp), 'yyyy-MM-dd');
      const startDate = config.startDate ? format(parseISO(config.startDate), 'yyyy-MM-dd') : null;
      const endDate = config.endDate ? format(parseISO(config.endDate), 'yyyy-MM-dd') : null;

      if (startDate && msgDate < startDate) return false;
      if (endDate && msgDate > endDate) return false;
      return true;
    });
    
    this.logger.debug(`过滤后消息数量: ${filtered.length}`);
    return filtered;
  }

  private async generateAISummary(messages: ChatMessage[], keywords: string[]): Promise<string> {
    try {
      const apiKey = this.config.modules.aiSummary.cursorApiKey;
      if (!apiKey) {
        this.logger.error('未配置Cursor API密钥，无法生成AI总结');
        return this.generateBasicSummary(messages, keywords);
      }
      
      const prompt = this.buildPrompt(messages, keywords);
      this.logger.debug(`已生成AI总结提示词，长度: ${prompt.length}字符`);
      
      this.logger.debug(`正在调用Cursor API: ${this.config.modules.aiSummary.cursorApiUrl}`);
      const response = await axios.post(
        this.config.modules.aiSummary.cursorApiUrl,
        {
          messages: [
            {
              role: 'system',
              content: '你是一个专业的聊天记录总结助手，请根据提供的微信群聊消息生成简洁的总结。重点提取有价值的信息和讨论要点。'
            },
            {
              role: 'user',
              content: prompt
            }
          ]
        },
        {
          headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      this.logger.stage('SUMMARY', StageLogType.SUCCESS, 'AI总结生成成功');
      return response.data.choices[0].message.content;
    } catch (error) {
      this.logger.stage('SUMMARY', StageLogType.FAILURE, 'AI总结生成失败', error);
      return this.generateBasicSummary(messages, keywords);
    }
  }

  private generateBasicSummary(messages: ChatMessage[], keywords: string[]): string {
    this.logger.debug('使用基本统计方法生成总结');
    
    // 当AI总结失败或禁用时的基本总结
    const messageCount = messages.length;
    const participantSet = new Set(messages.map(msg => msg.from));
    const participants = Array.from(participantSet);
    
    // 统计每个人发言次数
    const speakerCounts: {[key: string]: number} = {};
    messages.forEach(msg => {
      speakerCounts[msg.from] = (speakerCounts[msg.from] || 0) + 1;
    });
    
    // 找出前3个最活跃的发言人
    const topSpeakers = Object.entries(speakerCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([name, count]) => `${name}(${count}条)`);
    
    // 关键词统计
    const keywordMatches = this.countKeywordMatches(messages, keywords);
    const keywordSummary = Object.entries(keywordMatches)
      .map(([keyword, count]) => `"${keyword}"(${count}次)`)
      .join(', ');
    
    // 生成基本总结
    const timeRange = `${format(new Date(messages[0]?.timestamp || Date.now()), 'MM-dd HH:mm')} 至 ${format(new Date(messages[messages.length-1]?.timestamp || Date.now()), 'MM-dd HH:mm')}`;
    
    let summary = `时间范围: ${timeRange}\n`;
    summary += `消息总数: ${messageCount}条\n`;
    summary += `参与人数: ${participants.length}人\n`;
    summary += `活跃成员: ${topSpeakers.join(', ')}\n`;
    
    if (keywords.length > 0) {
      summary += `关键词出现: ${keywordSummary || "无匹配关键词"}\n`;
    }
    
    this.logger.debug('基本统计总结已生成');
    return summary;
  }

  private countKeywordMatches(messages: ChatMessage[], keywords: string[]): {[keyword: string]: number} {
    const result: {[keyword: string]: number} = {};
    
    keywords.forEach(keyword => {
      result[keyword] = 0;
      messages.forEach(msg => {
        if (msg.content.includes(keyword)) {
          result[keyword]++;
        }
      });
    });
    
    return result;
  }

  private buildPrompt(messages: ChatMessage[], keywords: string[]): string {
    // 准备消息数据
    const messagesText = messages
      .map(msg => {
        const time = format(new Date(msg.timestamp), 'HH:mm:ss');
        const sender = msg.from;
        return `[${time}] ${sender}: ${msg.content}`;
      })
      .join('\n');
    
    // 使用配置的提示词模板
    let prompt = this.config.modules.aiSummary.summaryPrompt.replace('{{messages}}', messagesText);
    
    // 添加关键词指示
    if (keywords && keywords.length > 0) {
      prompt += `\n\n特别关注以下关键词: ${keywords.join(', ')}`;
    }
    
    return prompt;
  }
  
  private async saveSummary(summary: SummaryResult, config: SummaryConfig): Promise<void> {
    try {
      // 创建群组目录
      const sanitizedGroupName = config.groupName.replace(/[\\/:*?"<>|]/g, '_');
      const groupFolder = path.join(this.summaryStoragePath, sanitizedGroupName);
      fs.mkdirSync(groupFolder, { recursive: true });
      
      // 确定文件名 (使用开始日期)
      const baseFileName = summary.dateRange.start;
      const jsonFilePath = path.join(groupFolder, `${baseFileName}.json`);
      
      // 保存JSON格式
      await fs.promises.writeFile(
        jsonFilePath,
        JSON.stringify(summary, null, 2)
      );
      
      this.logger.debug(`总结已保存为JSON: ${jsonFilePath}`);
      
      // 获取配置的导出格式
      const exportFormats = config.outputFormat 
        ? [config.outputFormat]
        : this.config.storage.exportFormats;
        
      // 导出各种格式
      for (const format of exportFormats) {
        if (format.toLowerCase() === 'json') continue; // 已经保存为JSON
        
        await this.exportSummaryInFormat(summary, format, groupFolder);
      }
      
      this.logger.stage('SUMMARY', StageLogType.SUCCESS, `总结已保存到 ${groupFolder}，格式: ${exportFormats.join(', ')}`);
    } catch (error) {
      this.logger.stage('SUMMARY', StageLogType.FAILURE, '保存总结失败', error);
    }
  }
  
  private async exportSummaryInFormat(summary: SummaryResult, format: string, outputFolder: string): Promise<void> {
    try {
      const baseFileName = summary.dateRange.start;
      let content = '';
      let filePath = '';
      
      switch (format.toLowerCase()) {
        case 'txt':
          content = this.formatSummaryAsTxt(summary);
          filePath = path.join(outputFolder, `${baseFileName}.txt`);
          await fs.promises.writeFile(filePath, content);
          this.logger.debug(`总结已导出为TXT: ${filePath}`);
          break;
          
        case 'md':
          content = this.formatSummaryAsMarkdown(summary);
          filePath = path.join(outputFolder, `${baseFileName}.md`);
          await fs.promises.writeFile(filePath, content);
          this.logger.debug(`总结已导出为Markdown: ${filePath}`);
          break;
          
        default:
          this.logger.warn(`不支持的导出格式: ${format}`);
          break;
      }
    } catch (error) {
      this.logger.error(`导出 ${format} 格式失败`, error);
    }
  }
  
  private formatSummaryAsTxt(summary: SummaryResult): string {
    let result = `微信群聊总结\n`;
    result += `============================\n`;
    result += `群名: ${summary.groupName}\n`;
    result += `日期: ${summary.dateRange.start} 至 ${summary.dateRange.end}\n`;
    result += `消息数: ${summary.messageCount}\n`;
    
    if (summary.keywords.length > 0) {
      result += `关键词: ${summary.keywords.join(', ')}\n`;
      
      if (summary.keywordMatches && Object.keys(summary.keywordMatches).length > 0) {
        result += `\n关键词匹配:\n`;
        Object.entries(summary.keywordMatches).forEach(([keyword, count]) => {
          result += `- ${keyword}: ${count}次\n`;
        });
      }
    }
    
    result += `============================\n\n`;
    result += summary.summary;
    return result;
  }
  
  private formatSummaryAsMarkdown(summary: SummaryResult): string {
    let result = `# 微信群聊总结 - ${summary.groupName}\n\n`;
    result += `## 基本信息\n\n`;
    result += `- **群名**: ${summary.groupName}\n`;
    result += `- **日期范围**: ${summary.dateRange.start} 至 ${summary.dateRange.end}\n`;
    result += `- **消息总数**: ${summary.messageCount}\n`;
    
    if (summary.keywords.length > 0) {
      result += `- **关注关键词**: ${summary.keywords.join(', ')}\n`;
      
      if (summary.keywordMatches && Object.keys(summary.keywordMatches).length > 0) {
        result += `\n## 关键词匹配\n\n`;
        Object.entries(summary.keywordMatches).forEach(([keyword, count]) => {
          result += `- **${keyword}**: ${count}次\n`;
        });
      }
    }
    
    result += `\n## 总结内容\n\n${summary.summary}\n`;
    
    result += `\n\n---\n*由微信聊天记录总结工具自动生成于 ${format(new Date(), 'yyyy-MM-dd HH:mm:ss')}*`;
    
    return result;
  }
  
  public isEnabled(): boolean {
    return this.aiSummaryEnabled;
  }
} 