export interface ChatMessage {
  id: string;
  from: string;
  to: string;
  content: string;
  timestamp: number;
  type: string;
}

export interface SummaryConfig {
  keywords?: string[];
  startDate?: string;
  endDate?: string;
  groupName: string;
}

export interface SummaryResult {
  summary: string;
  keywords: string[];
  dateRange: {
    start: string;
    end: string;
  };
} 