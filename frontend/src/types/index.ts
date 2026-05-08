export interface TokenResponse {
  token: string;
  url: string;
}

export interface ToolStatusEvent {
  tool: string;
  status: "in_progress" | "completed";
  data?: Record<string, unknown>;
}

export interface CallSummaryData {
  summary: string;
  appointments: Array<{
    date: string;
    time: string;
    status: string;
  }>;
  preferences: string[];
  intent: string;
  timestamp: string;
}

export type AgentState = "idle" | "listening" | "thinking" | "speaking";

export interface ToolCallLog {
  tool: string;
  status: string;
  timestamp: Date;
  data?: Record<string, unknown>;
}
