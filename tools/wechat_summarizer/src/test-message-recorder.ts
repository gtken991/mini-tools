import { loadConfig } from './config/config';
import { WeChatMCPService } from './services/wechat-mcp';
import { Logger, StageLogType } from './services/logger';
import { format, subDays } from 'date-fns';
import * as path from 'path';
import * as fs from 'fs';

/**
 * 测试微信消息获取和记录功能
 * 
 * 该脚本专门用于测试微信聊天记录的获取和保存功能，不包含AI总结功能
 * 使用 ./config.yaml 配置文件
 */
async function main() {
  try {
    console.log('启动微信消息获取测试...');
    
    // 加载配置文件
    const config = loadConfig('./config.yaml');
    
    // 初始化日志系统
    const logger = new Logger(config);
    logger.stage('TEST', StageLogType.START, '微信消息获取测试启动', {
      mcpEnabled: config.modules.mcpClient.enabled,
      messageRecordingEnabled: config.modules.messageRecording.enabled,
      aiSummaryEnabled: config.modules.aiSummary.enabled,
      groupNames: config.wechat.groupNames
    });
    
    // 初始化微信MCP服务
    const wechatService = new WeChatMCPService(config, logger);
    
    // 设置消息接收监听器
    wechatService.on('message', (message) => {
      logger.stage('TEST', StageLogType.PROGRESS, '收到新消息', {
        group: message.roomName,
        from: message.from,
        content: message.content.substring(0, 30) + (message.content.length > 30 ? '...' : '')
      });
    });
    
    // 设置关键词匹配监听器
    wechatService.on('keyword_matched', (event) => {
      const { message, keywords } = event;
      logger.stage('TEST', StageLogType.PROGRESS, '关键词匹配', {
        group: message.roomName,
        from: message.from,
        keywords,
        content: message.content.substring(0, 30) + (message.content.length > 30 ? '...' : '')
      });
    });
    
    // 启动微信服务
    await wechatService.start();
    logger.stage('TEST', StageLogType.SUCCESS, '微信MCP服务启动成功');
    
    // 显示历史消息样本 - 今天的消息
    await displayMessageSamples(wechatService, config, logger, 0); // 今天
    
    // 显示历史消息样本 - 昨天的消息
    await displayMessageSamples(wechatService, config, logger, 1); // 昨天
    
    // 显示历史消息样本 - 前天的消息
    await displayMessageSamples(wechatService, config, logger, 2); // 前天
    
    // 打印聊天记录文件信息
    printMessageFilesInfo(config, logger);
    
    // 显示定期消息统计的定时器
    startPeriodicMessageStats(wechatService, config, logger);
    
    logger.stage('TEST', StageLogType.SUCCESS, '测试程序初始化完成，现在开始监听新消息...');
    logger.info('按 Ctrl+C 停止程序');
    
    // 设置退出处理程序
    setupCleanupHandlers(wechatService, logger);
  } catch (error) {
    console.error('测试启动失败:', error);
    process.exit(1);
  }
}

async function displayMessageSamples(wechatService: WeChatMCPService, config: any, logger: Logger, daysAgo: number) {
  const date = format(subDays(new Date(), daysAgo), 'yyyy-MM-dd');
  const dateLabel = daysAgo === 0 ? '今天' : daysAgo === 1 ? '昨天' : `${daysAgo}天前`;
  
  logger.stage('TEST', StageLogType.PROGRESS, `获取${dateLabel}(${date})的消息样本`);
  
  for (const groupName of config.wechat.groupNames) {
    try {
      const messages = await wechatService.getMessagesByDate(groupName, date);
      
      if (messages.length > 0) {
        logger.info(`群 "${groupName}" 在 ${date} 有 ${messages.length} 条消息`);
        
        // 获取前N条消息样本
        const sampleCount = Math.min(config.modules.mcpClient.sampleMessageCount, messages.length);
        const samples = messages.slice(0, sampleCount);
        
        // 在控制台显示样本
        let sampleText = `===== 群 "${groupName}" ${dateLabel}(${date})的消息样例 (${sampleCount}/${messages.length}) =====\n`;
        samples.forEach((msg, idx) => {
          const time = format(new Date(msg.timestamp), 'HH:mm:ss');
          sampleText += `${idx + 1}. [${time}] ${msg.from}: ${msg.content.substring(0, 50)}${msg.content.length > 50 ? '...' : ''}\n`;
        });
        sampleText += '===========================================\n';
        
        logger.info(sampleText);
      } else {
        logger.info(`群 "${groupName}" 在 ${date} 没有消息记录`);
      }
    } catch (error) {
      logger.error(`获取群 "${groupName}" 的消息样本失败`, error);
    }
  }
}

function printMessageFilesInfo(config: any, logger: Logger) {
  const messageBasePath = path.join(config.storage.basePath, config.storage.messageDir);
  
  try {
    if (!fs.existsSync(messageBasePath)) {
      logger.warn(`消息存储目录 ${messageBasePath} 不存在`);
      return;
    }
    
    // 获取所有群组目录
    const groupDirs = fs.readdirSync(messageBasePath, { withFileTypes: true })
      .filter(dirent => dirent.isDirectory())
      .map(dirent => dirent.name);
    
    if (groupDirs.length === 0) {
      logger.info('尚未发现群消息存储目录');
      return;
    }
    
    logger.stage('TEST', StageLogType.PROGRESS, `发现 ${groupDirs.length} 个群的消息存储目录`);
    
    // 遍历每个群组目录
    for (const groupDir of groupDirs) {
      const groupPath = path.join(messageBasePath, groupDir);
      const files = fs.readdirSync(groupPath)
        .filter(file => file.endsWith('.json'))
        .sort((a, b) => b.localeCompare(a)); // 按日期降序排列
      
      logger.info(`群 "${groupDir}" 有 ${files.length} 个消息文件:`);
      
      // 显示每个文件的信息
      for (const file of files) {
        const filePath = path.join(groupPath, file);
        const stats = fs.statSync(filePath);
        const fileContent = fs.readFileSync(filePath, 'utf8');
        let messages = [];
        
        try {
          messages = JSON.parse(fileContent);
        } catch (error) {
          logger.error(`解析文件 ${filePath} 失败`, error);
          continue;
        }
        
        logger.info(`  - ${file}: ${messages.length} 条消息, ${(stats.size / 1024).toFixed(2)} KB`);
      }
    }
  } catch (error) {
    logger.error('获取消息文件信息失败', error);
  }
}

function startPeriodicMessageStats(wechatService: WeChatMCPService, config: any, logger: Logger) {
  // 每30秒统计一次当天的消息数量
  const interval = setInterval(async () => {
    const today = format(new Date(), 'yyyy-MM-dd');
    logger.stage('TEST', StageLogType.PROGRESS, `定期统计 ${today} 的消息数量`);
    
    for (const groupName of config.wechat.groupNames) {
      try {
        const messages = await wechatService.getMessagesByDate(groupName, today);
        logger.info(`群 "${groupName}" 今日消息数量: ${messages.length}`);
        
        if (messages.length > 0) {
          const lastMessage = messages[messages.length - 1];
          const lastMessageTime = format(new Date(lastMessage.timestamp), 'HH:mm:ss');
          logger.info(`最后一条消息时间: ${lastMessageTime}, 发送者: ${lastMessage.from}`);
        }
      } catch (error) {
        logger.error(`获取群 "${groupName}" 的当日消息统计失败`, error);
      }
    }
  }, 30000); // 30秒
  
  return interval;
}

function setupCleanupHandlers(wechatService: WeChatMCPService, logger: Logger) {
  let isCleaningUp = false;
  
  const cleanup = async () => {
    if (isCleaningUp) return;
    isCleaningUp = true;
    
    logger.stage('TEST', StageLogType.PROGRESS, '正在关闭测试程序...');
    
    try {
      // 停止微信服务
      await wechatService.stop();
      logger.stage('TEST', StageLogType.SUCCESS, '微信MCP服务已关闭');
      
      // 关闭日志
      logger.stage('TEST', StageLogType.COMPLETE, '测试程序已安全关闭');
      logger.close();
    } catch (error) {
      console.error('关闭程序时出错:', error);
    }
    
    process.exit();
  };
  
  // 注册信号处理
  process.on('SIGINT', cleanup);
  process.on('SIGTERM', cleanup);
  
  // 处理未捕获的异常
  process.on('uncaughtException', async (error) => {
    logger.stage('TEST', StageLogType.FAILURE, '未捕获的异常', error);
    await cleanup();
  });
  
  // 处理未处理的Promise拒绝
  process.on('unhandledRejection', async (reason) => {
    logger.stage('TEST', StageLogType.FAILURE, '未处理的Promise拒绝', reason);
    await cleanup();
  });
}

// 启动测试程序
main().catch(error => {
  console.error('测试程序启动失败:', error);
  process.exit(1);
}); 