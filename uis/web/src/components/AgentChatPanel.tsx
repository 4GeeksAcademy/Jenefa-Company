"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { agentWebSocketUrl, AgentFrame } from "@/lib/agentWebSocket";

type ChatMessage = {
  id: string;
  role: "user" | "agent";
  text: string;
  status?: "streaming" | "interrupted" | "completed";
};

function newId(prefix: string): string {
  return `${prefix}-${crypto.randomUUID()}`;
}

export function AgentChatPanel() {
  const [sessionId] = useState(() => newId("session"));
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [connected, setConnected] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttempt = useRef(0);

  useEffect(() => {
    let closed = false;
    const connect = () => {
      if (closed) return;
      const socket = new WebSocket(agentWebSocketUrl(sessionId, sessionId));
      socketRef.current = socket;
      socket.onopen = () => {
        reconnectAttempt.current = 0;
        setConnected(true);
      };
      socket.onmessage = (event) => {
        const frame = JSON.parse(event.data) as AgentFrame;
        if (!frame.message_id) return;
        if (frame.type === "token_chunk") {
          setMessages((current) =>
            current.map((message) =>
              message.id === frame.message_id
                ? { ...message, text: message.text + (frame.text ?? ""), status: "streaming" }
                : message
            )
          );
        }
        if (frame.type === "generation_completed" || frame.type === "generation_interrupted") {
          setMessages((current) =>
            current.map((message) =>
              message.id === frame.message_id
                ? { ...message, status: frame.type === "generation_interrupted" ? "interrupted" : "completed" }
                : message
            )
          );
          setActiveId((current) => (current === frame.message_id ? null : current));
        }
      };
      socket.onclose = () => {
        setConnected(false);
        if (!closed) {
          const delay = Math.min(8000, 500 * 2 ** reconnectAttempt.current++);
          reconnectTimer.current = setTimeout(connect, delay);
        }
      };
    };
    connect();
    return () => {
      closed = true;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      socketRef.current?.close();
    };
  }, [sessionId]);

  function submit(event: FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || !connected || !socketRef.current) return;
    const id = newId("turn");
    setMessages((current) => [
      ...current,
      { id: newId("user"), role: "user", text },
      { id, role: "agent", text: "", status: "streaming" },
    ]);
    setActiveId(id);
    socketRef.current.send(JSON.stringify({ type: "message", message_id: id, text }));
    setDraft("");
  }

  function interrupt() {
    if (!activeId || !socketRef.current) return;
    socketRef.current.send(JSON.stringify({ type: "interrupt", message_id: activeId }));
    setMessages((current) =>
      current.map((message) =>
        message.id === activeId ? { ...message, status: "interrupted" } : message
      )
    );
  }

  return (
    <section className="mx-auto w-full max-w-4xl">
      <div className="mb-6 flex items-end justify-between border-b border-border pb-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Operations assistant</p>
          <h2 className="font-display text-3xl text-foreground">Live support chat</h2>
        </div>
        <p className="text-sm text-muted">{connected ? "Connected" : "Reconnecting"}</p>
      </div>
      <div className="min-h-[24rem] space-y-4 border border-border bg-surface p-5">
        {messages.length === 0 ? <p className="text-sm text-muted">Ask about HealthCore operations, clinical workflows, or compliance.</p> : null}
        {messages.map((message) => (
          <div key={message.id} className={message.role === "user" ? "ml-auto max-w-[80%] text-right" : "max-w-[80%]"}>
            <p className="mb-1 text-xs uppercase tracking-[0.12em] text-muted">{message.role === "user" ? "You" : "Assistant"}</p>
            <p className={`whitespace-pre-wrap text-sm ${message.status === "interrupted" ? "border-l-2 border-amber-500 pl-3 text-muted" : "text-foreground"}`}>
              {message.text || (message.status === "streaming" ? "..." : "")}
            </p>
            {message.status === "interrupted" ? <p className="mt-1 text-xs text-amber-700">Interrupted</p> : null}
          </div>
        ))}
      </div>
      <form onSubmit={submit} className="mt-4 flex gap-3">
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Write a message"
          className="min-w-0 flex-1 border border-border bg-white px-3 py-2 text-sm text-foreground outline-none focus:border-sidebar"
          aria-label="Message"
        />
        <button type="submit" disabled={!connected || !draft.trim()} className="bg-sidebar px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
          Send
        </button>
        <button type="button" onClick={interrupt} disabled={!activeId} className="border border-border px-4 py-2 text-sm font-medium text-foreground disabled:opacity-50">
          Interrupt
        </button>
      </form>
    </section>
  );
}