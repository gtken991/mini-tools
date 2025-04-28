import { Wechat4u } from 'wechat4u';
import { ChatMessage } from '../types';
import * as fs from 'fs';
import * as path from 'path';
import { format } from 'date-fns';

export class WeChatService {
  private bot: Wechat4u;
  private storagePath: string;
  private targetGroup: string;

  constructor(storagePath: string, targetGroup: string) {
    this.storagePath = storagePath;
    this.targetGroup = targetGroup;
    this.bot = new Wechat4u();
    this.initializeStorage();
  }

  private initializeStorage() {
    if (!fs.existsSync(this.storagePath)) {
      fs.mkdirSync(this.storagePath, { recursive: true });
    }
  }

  public async start() {
    await this.bot.start();
    this.bot.on('message', async (msg: any) => {
      if (msg.type === 1 && msg.from === this.targetGroup) {
        await this.saveMessage(msg);
      }
    });
  }

  private async saveMessage(msg: any) {
    const date = format(new Date(), 'yyyy-MM-dd');
    const filePath = path.join(this.storagePath, `${date}.json`);
    
    const message: ChatMessage = {
      id: msg.id,
      from: msg.from,
      to: msg.to,
      content: msg.content,
      timestamp: msg.timestamp,
      type: msg.type
    };

    let messages: ChatMessage[] = [];
    if (fs.existsSync(filePath)) {
      const content = await fs.promises.readFile(filePath, 'utf-8');
      messages = JSON.parse(content);
    }

    messages.push(message);
    await fs.promises.writeFile(filePath, JSON.stringify(messages, null, 2));
  }

  public async getMessagesByDate(date: string): Promise<ChatMessage[]> {
    const filePath = path.join(this.storagePath, `${date}.json`);
    if (!fs.existsSync(filePath)) {
      return [];
    }

    const content = await fs.promises.readFile(filePath, 'utf-8');
    return JSON.parse(content);
  }
} 