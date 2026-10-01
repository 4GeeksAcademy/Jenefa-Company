import { API_BASE } from "@/lib/api";
import { getAuthToken } from "@/lib/authStorage";

export type AgentFrame = {
  type: "token_chunk" | "generation_completed" | "generation_interrupted" | "error";
  session_id: string;
  thread_id: string;
  message_id?: string;
  text?: string;
  error?: string;
};

export function agentWebSocketUrl(sessionId: string, threadId: string): string {
  const base = API_BASE.startsWith("https://")
    ? API_BASE.replace("https://", "wss://")
    : API_BASE.replace("http://", "ws://");
  const params = new URLSearchParams({
    token: getAuthToken() ?? "",
    session_id: sessionId,
    thread_id: threadId,
  });
  return `${base}/agent/ws?${params.toString()}`;
}
