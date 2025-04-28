import axios from 'axios';
import { ChatMessage, SummaryConfig, SummaryResult } from '../types';
import { format, parseISO } from 'date-fns';

export class SummaryService {
  private apiKey: string;
  private apiUrl: string;

  constructor(apiKey: string, apiUrl: string) {
    this.apiKey = apiKey;
    this.apiUrl = apiUrl;
  }

  public async summarize(messages: ChatMessage[], config: SummaryConfig): Promise<SummaryResult> {
    const filteredMessages = this.filterMessages(messages, config);
    const summary = await this.generateSummary(filteredMessages, config.keywords);

    return {
      summary,
      keywords: config.keywords || [],
      dateRange: {
        start: config.startDate || format(filteredMessages[0]?.timestamp || new Date(), 'yyyy-MM-dd'),
        end: config.endDate || format(filteredMessages[filteredMessages.length - 1]?.timestamp || new Date(), 'yyyy-MM-dd')
      }
    };
  }

  private filterMessages(messages: ChatMessage[], config: SummaryConfig): ChatMessage[] {
    return messages.filter(msg => {
      const msgDate = format(msg.timestamp, 'yyyy-MM-dd');
      const startDate = config.startDate ? format(parseISO(config.startDate), 'yyyy-MM-dd') : null;
      const endDate = config.endDate ? format(parseISO(config.endDate), 'yyyy-MM-dd') : null;

      if (startDate && msgDate < startDate) return false;
      if (endDate && msgDate > endDate) return false;
      return true;
    });
  }

  private async generateSummary(messages: ChatMessage[], keywords?: string[]): Promise<string> {
    const prompt = this.buildPrompt(messages, keywords);
    
    try {
      const response = await axios.post(
        this.apiUrl,
        {
          messages: [
            {
              role: 'system',
              content: '你是一个专业的聊天记录总结助手，请根据提供的聊天记录生成简洁的总结。'
            },
            {
              role: 'user',
              content: prompt
            }
          ]
        },
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      return response.data.choices[0].message.content;
    } catch (error) {
      console.error('Error generating summary:', error);
      throw new Error('Failed to generate summary');
    }
  }

  private buildPrompt(messages: ChatMessage[], keywords?: string[]): string {
    const messagesText = messages
      .map(msg => `${format(msg.timestamp, 'HH:mm:ss')} ${msg.from}: ${msg.content}`)
      .join('\n');

    let prompt = `请总结以下聊天记录：\n\n${messagesText}\n\n`;
    
    if (keywords && keywords.length > 0) {
      prompt += `特别关注以下关键词：${keywords.join(', ')}\n`;
    }

    return prompt;
  }
} 