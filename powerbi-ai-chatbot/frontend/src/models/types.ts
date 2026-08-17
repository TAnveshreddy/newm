/** Types mirroring the backend contract (backend/src/models/types.ts). */

export type VisualType =
  | 'kpi'
  | 'table'
  | 'bar'
  | 'column'
  | 'line'
  | 'pie'
  | 'donut'
  | 'stacked';

export interface QueryFilter {
  field: string;
  operator: string;
  value: string | number | boolean | Array<string | number>;
}

export interface VisualSpec {
  type: VisualType;
  title: string;
  category?: string;
  measures: string[];
  filters?: QueryFilter[];
  stacked?: boolean;
}

export interface ResultColumn {
  name: string;
  role: 'dimension' | 'measure';
  dataType: string;
}

export interface QueryResult {
  columns: ResultColumn[];
  rows: Array<Array<string | number | boolean | null>>;
  rowCount: number;
  durationMs: number;
  truncated: boolean;
}

export type ChatResponseStatus =
  | 'answer'
  | 'visual'
  | 'clarification'
  | 'unavailable'
  | 'error';

export interface ChatResponse {
  conversationId: string;
  status: ChatResponseStatus;
  intent: string;
  message: string;
  visual?: VisualSpec;
  result?: QueryResult;
  clarification?: string;
}

export interface ModelSummary {
  modelId: string;
  displayName: string;
  description?: string;
}

export interface UserProfile {
  userId: string;
  username: string;
  name?: string;
  roles: string[];
  groups: string[];
}

/** A chat message rendered in the UI. */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  visual?: VisualSpec;
  result?: QueryResult;
  status?: ChatResponseStatus;
}
