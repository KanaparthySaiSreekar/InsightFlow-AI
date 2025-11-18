export interface User {
  id: number;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface LLMConfig {
  id: number;
  provider: 'openai' | 'google' | 'anthropic';
  is_active: number;
  created_at: string;
}

export interface Project {
  id: number;
  name: string;
  description?: string;
  original_filename?: string;
  schema_json?: string;
  created_at: string;
  updated_at?: string;
}

export interface Chat {
  id: number;
  project_id: number;
  title?: string;
  created_at: string;
  messages?: Message[];
}

export interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  sql_query?: string;
  query_result?: string;
  error_message?: string;
  created_at: string;
}

export interface ChatQueryResponse {
  message: Message;
  data?: any[];
  visualization_type?: 'bar' | 'line' | 'pie' | 'scatter' | 'table';
}
