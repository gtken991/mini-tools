import { config } from 'dotenv';
import { WeChatService } from './services/wechat';
import { SummaryService } from './services/summary';
import { format } from 'date-fns';

// 加载环境变量
config();

const wechatService = new WeChatService(
  process.env.WECHAT_STORAGE_PATH || './data/wechat',
  process.env.TARGET_GROUP_NAME || ''
);

const summaryService = new SummaryService(
  process.env.CURSOR_API_KEY || '',
  process.env.CURSOR_API_URL || ''
);

async function main() {
  try {
    // 启动微信服务
    await wechatService.start();
    console.log('WeChat service started');

    // 示例：获取今天的消息并总结
    const today = format(new Date(), 'yyyy-MM-dd');
    const messages = await wechatService.getMessagesByDate(today);
    
    const summary = await summaryService.summarize(messages, {
      groupName: process.env.TARGET_GROUP_NAME || '',
      keywords: ['重要', '紧急', '会议']
    });

    console.log('Summary:', summary);
  } catch (error) {
    console.error('Error:', error);
  }
}

main(); 