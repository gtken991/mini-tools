export interface ChatMessage {
  id: string;
  from: string;
  to?: string;          // 可选，兼容旧数据
  roomId?: string;      // 群聊ID
  roomName?: string;    // 群聊名称
  content: string;
  timestamp: number;
  type: string;
}

export interface SummaryConfig {
  keywords?: string[];
  startDate?: string;
  endDate?: string;
  groupName: string;
  enableAI?: boolean;    // 是否启用AI总结
  maxMessages?: number;  // 最大处理消息数
  outputFormat?: string; // 输出格式
}

export interface SummaryResult {
  summary: string;
  keywords: string[];
  dateRange: {
    start: string;
    end: string;
  };
  groupName: string;
  messageCount: number;
  keywordMatches?: {
    [keyword: string]: number;
  };
}

export interface KeywordMatchEvent {
  message: ChatMessage;
  keywords: string[];
} 