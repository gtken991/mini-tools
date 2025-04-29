import { loadConfig } from './config/config';
import { WeChatMCPService } from './services/wechat-mcp';
import { SummaryService } from './services/summary';
import { Logger, StageLogType } from './services/logger';
import { format, subDays } from 'date-fns';
import * as path from 'path';
import * as fs from 'fs';

async function main() {
  try {
    // 加载配置
    const config = loadConfig('./config.yaml');
    
    // 初始化日志系统
    const logger = new Logger(config);
    logger.stage('SYSTEM', StageLogType.START, '加载配置完成', {
      messageRecording: config.modules.messageRecording.enabled,
      mcpClient: config.modules.mcpClient.enabled,
      aiSummary: config.modules.aiSummary.enabled
    });
    
    // 初始化服务
    const wechatService = new WeChatMCPService(config, logger);
    const summaryService = new SummaryService(config, logger);
    
    // 定时任务管理
    let summaryIntervals: NodeJS.Timeout[] = [];
    
    // 启动服务
    await startServices(wechatService, summaryService, config, logger, summaryIntervals);
    
    // 处理进程退出
    setupCleanupHandlers(wechatService, logger, summaryIntervals);
    
    logger.stage('SYSTEM', StageLogType.SUCCESS, '系统初始化完成，服务已启动');
  } catch (error) {
    console.error('系统启动失败:', error);
    process.exit(1);
  }
}

async function startServices(
  wechatService: WeChatMCPService, 
  summaryService: SummaryService, 
  config: any, 
  logger: Logger,
  summaryIntervals: NodeJS.Timeout[]
) {
  try {
    // 启动微信服务
    if (config.modules.mcpClient.enabled) {
      await wechatService.start();
      logger.info('微信MCP服务已启动');
      
      // 注册消息处理事件
      wechatService.on('message', (message) => {
        if (config.modules.mcpClient.logMessageContent) {
          const truncatedContent = message.content.length > 20 
            ? `${message.content.substring(0, 20)}...` 
            : message.content;
          logger.info(`接收到来自${message.roomName}的消息: ${message.from.substring(0, 2)}***: ${truncatedContent}`);
        }
      });
      
      // 注册关键词匹配事件
      if (config.keywords.enabled) {
        wechatService.on('keyword_matched', (event) => {
          const { message, keywords } = event;
          logger.info(`[关键词匹配] 群：${message.roomName}, 发送者: ${message.from}, 关键词: ${keywords.join(', ')}`);
        });
        logger.debug('关键词监控已启用');
      }
    } else {
      logger.warn('MCP客户端已禁用，跳过启动');
    }
    
    // 初始展示历史消息样例（当禁用AI总结但启用了MCP客户端时）
    if (config.modules.mcpClient.enabled && !config.modules.aiSummary.enabled && config.modules.mcpClient.showSampleMessages) {
      await showMessageSamples(wechatService, config, logger);
    }
    
    // 设置定时总结任务
    if (config.modules.aiSummary.enabled && config.modules.messageRecording.enabled) {
      setupSummaryTasks(wechatService, summaryService, config, logger, summaryIntervals);
      
      // 初始生成一次总结（获取前一天的消息）
      await generateInitialSummaries(wechatService, summaryService, config, logger);
    } else if (config.modules.aiSummary.enabled && !config.modules.messageRecording.enabled) {
      logger.warn('消息记录功能已禁用，无法启用AI总结定时任务');
    }
    
    logger.stage('SYSTEM', StageLogType.SUCCESS, '所有服务启动完成');
  } catch (error) {
    logger.stage('SYSTEM', StageLogType.FAILURE, '服务启动失败', error);
    throw error;
  }
}

async function showMessageSamples(wechatService: WeChatMCPService, config: any, logger: Logger) {
  logger.info('获取消息样例以验证MCP连接...');
  
  for (const groupName of config.wechat.groupNames) {
    try {
      // 获取今天和昨天的消息
      const today = format(new Date(), 'yyyy-MM-dd');
      const yesterday = format(subDays(new Date(), 1), 'yyyy-MM-dd');
      
      // 先尝试获取今天的消息
      let messages = await wechatService.getMessagesByDate(groupName, today);
      
      // 如果今天没有消息，尝试获取昨天的
      if (messages.length === 0) {
        messages = await wechatService.getMessagesByDate(groupName, yesterday);
        logger.debug(`今日无消息，获取到 ${messages.length} 条昨日消息`);
      } else {
        logger.debug(`获取到 ${messages.length} 条今日消息`);
      }
      
      // 如果仍然没有消息，记录日志
      if (messages.length === 0) {
        logger.warn(`群 ${groupName} 没有最近消息`);
      }
    } catch (error) {
      logger.error(`获取群 ${groupName} 的样例消息失败`, error);
    }
  }
}

function setupSummaryTasks(
  wechatService: WeChatMCPService, 
  summaryService: SummaryService, 
  config: any, 
  logger: Logger,
  summaryIntervals: NodeJS.Timeout[]
) {
  // 先清除所有已有的定时任务
  summaryIntervals.forEach(interval => clearInterval(interval));
  summaryIntervals.length = 0;
  
  logger.stage('SUMMARY', StageLogType.START, '设置定时总结任务');
  
  // 为每个群设置定时总结
  for (const groupName of config.wechat.groupNames) {
    const interval = setInterval(async () => {
      try {
        // 获取当天的消息
        const today = format(new Date(), 'yyyy-MM-dd');
        const messages = await wechatService.getMessagesByDate(groupName, today);
        
        if (messages.length > 0) {
          logger.stage('SUMMARY', StageLogType.PROGRESS, `开始为群 ${groupName} 生成今日总结`, {
            messageCount: messages.length,
            date: today
          });
          
          // 生成总结
          const summary = await summaryService.summarize(messages, {
            groupName,
            keywords: config.keywords.enabled ? config.keywords.words : [],
            enableAI: config.modules.aiSummary.enabled,
            outputFormat: 'md'  // 同时生成Markdown格式
          });
          
          logger.stage('SUMMARY', StageLogType.SUCCESS, `群 ${groupName} 的总结已生成`, {
            length: summary.summary.length,
            date: today
          });
        } else {
          logger.debug(`群 ${groupName} 今日无新消息，跳过总结`);
        }
      } catch (error) {
        logger.stage('SUMMARY', StageLogType.FAILURE, `为群 ${groupName} 生成总结时出错`, error);
      }
    }, config.modules.aiSummary.summaryInterval * 60 * 1000); // 转换为毫秒
    
    summaryIntervals.push(interval);
    logger.info(`已为群 ${groupName} 设置 ${config.modules.aiSummary.summaryInterval} 分钟间隔的定时总结任务`);
  }
  
  logger.stage('SUMMARY', StageLogType.SUCCESS, '定时总结任务设置完成');
}

async function generateInitialSummaries(
  wechatService: WeChatMCPService, 
  summaryService: SummaryService, 
  config: any, 
  logger: Logger
) {
  logger.stage('SUMMARY', StageLogType.START, '生成初始总结（昨日数据）');
  
  // 为每个群生成前一天的总结
  for (const groupName of config.wechat.groupNames) {
    try {
      const yesterday = format(subDays(new Date(), 1), 'yyyy-MM-dd');
      const messages = await wechatService.getMessagesByDate(groupName, yesterday);
      
      if (messages.length > 0) {
        logger.info(`开始为群 ${groupName} 生成昨日(${yesterday})总结，共 ${messages.length} 条消息`);
        
        // 生成总结
        const summary = await summaryService.summarize(messages, {
          groupName,
          keywords: config.keywords.enabled ? config.keywords.words : [],
          startDate: yesterday,
          endDate: yesterday,
          enableAI: config.modules.aiSummary.enabled,
          outputFormat: 'md'  // 同时生成Markdown格式
        });
        
        logger.stage('SUMMARY', StageLogType.SUCCESS, `群 ${groupName} 的昨日总结已生成`, {
          length: summary.summary.length,
          date: yesterday
        });
      } else {
        logger.info(`群 ${groupName} 昨日无消息，跳过总结`);
      }
    } catch (error) {
      logger.stage('SUMMARY', StageLogType.FAILURE, `为群 ${groupName} 生成昨日总结时出错`, error);
    }
  }
  
  logger.stage('SUMMARY', StageLogType.COMPLETE, '初始总结生成完成');
}

function setupCleanupHandlers(
  wechatService: WeChatMCPService, 
  logger: Logger,
  summaryIntervals: NodeJS.Timeout[]
) {
  // 处理进程退出信号
  process.on('SIGINT', async () => {
    await cleanup(wechatService, logger, summaryIntervals);
    process.exit(0);
  });
  
  process.on('SIGTERM', async () => {
    await cleanup(wechatService, logger, summaryIntervals);
    process.exit(0);
  });
  
  // 处理未捕获的异常
  process.on('uncaughtException', async (error) => {
    logger.stage('SYSTEM', StageLogType.FAILURE, '发生未捕获的异常', error);
    await cleanup(wechatService, logger, summaryIntervals);
    process.exit(1);
  });
  
  // 处理未处理的Promise拒绝
  process.on('unhandledRejection', async (reason) => {
    logger.stage('SYSTEM', StageLogType.FAILURE, '发生未处理的Promise拒绝', reason);
    await cleanup(wechatService, logger, summaryIntervals);
    process.exit(1);
  });
}

async function cleanup(
  wechatService: WeChatMCPService, 
  logger: Logger,
  summaryIntervals: NodeJS.Timeout[]
) {
  logger.stage('SYSTEM', StageLogType.PROGRESS, '正在关闭服务...');
  
  // 清除所有定时任务
  summaryIntervals.forEach(interval => clearInterval(interval));
  logger.debug('已清除所有定时任务');
  
  // 停止服务
  if (wechatService.isEnabled()) {
    await wechatService.stop();
    logger.debug('已停止微信MCP服务');
  }
  
  // 关闭日志
  logger.stage('SYSTEM', StageLogType.COMPLETE, '服务已安全关闭');
  logger.close();
}

// 启动程序
main().catch(error => {
  console.error('程序启动失败:', error);
  process.exit(1);
}); 