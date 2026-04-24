export interface ChatRequest {
  message: string;
  conversation_id?: string | null;
}

export interface ChatResponse {
  answer: string;
  conversation_id?: string | null;
  sql: string[];
  rows: Record<string, unknown>[];
  warnings: string[];
}

export interface ChatMessage {
  role: 'assistant' | 'user';
  content: string;
  sql?: string[];
  rows?: Record<string, unknown>[];
  warnings?: string[];
  error?: boolean;
}
