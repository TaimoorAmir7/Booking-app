"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { api, getWsUrl } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { ChatMessage, ChatReply, ExtractedSlots } from "@/types";

type Props = {
  sessionId: string | null;
  onSessionCreated: (id: string) => void;
  onSlotsUpdate: (slots: ExtractedSlots, needsForm: boolean) => void;
  onAppointmentBooked: () => void;
};

export function ChatPanel({
  sessionId,
  onSessionCreated,
  onSlotsUpdate,
  onAppointmentBooked,
}: Props) {
  const { getAccessToken } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<"connecting" | "live" | "polling" | "offline">("offline");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [canConfirm, setCanConfirm] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const applyReply = useCallback(
    (reply: ChatReply) => {
      setMessages(reply.messages);
      onSlotsUpdate(reply.slots, reply.needs_form);
      setCanConfirm(Boolean(reply.slots?.complete));
      if (reply.appointment_id) onAppointmentBooked();
    },
    [onSlotsUpdate, onAppointmentBooked]
  );

  const sendViaRest = useCallback(
    async (content: string, confirm = false) => {
      const token = await getAccessToken();
      if (!token) return;
      setSending(true);
      setError(null);
      try {
        const reply = await api.sendChatMessage(token, {
          content,
          session_id: sessionId ?? undefined,
          confirm_booking: confirm,
        });
        if (!sessionId) onSessionCreated(reply.session_id);
        applyReply(reply);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to send message");
      } finally {
        setSending(false);
      }
    },
    [getAccessToken, sessionId, onSessionCreated, applyReply]
  );

  useEffect(() => {
    const activeSessionId = sessionId;
    if (!activeSessionId) {
      setStatus("offline");
      return;
    }

    const sid: string = activeSessionId;
    let cancelled = false;

    async function connect() {
      const token = await getAccessToken();
      if (!token || cancelled) return;

      const ws = new WebSocket(getWsUrl(sid, token));
      wsRef.current = ws;
      setStatus("connecting");

      ws.onopen = () => {
        if (!cancelled) setStatus("live");
      };

      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data as string);
          if (data.type === "connected") {
            setMessages(data.messages ?? []);
            return;
          }
          if (data.type === "chat.message") {
            applyReply(data as ChatReply);
            setSending(false);
            return;
          }
          if (data.type === "error") {
            setError(data.error ?? "WebSocket error");
            setSending(false);
          }
        } catch {
          setError("Invalid message from server");
        }
      };

      ws.onerror = () => {
        if (!cancelled) setStatus("polling");
      };

      ws.onclose = () => {
        if (!cancelled) setStatus("polling");
      };
    }

    connect();

    return () => {
      cancelled = true;
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [sessionId, getAccessToken, applyReply]);

  async function handleSend(content: string, confirm = false) {
    if (!content.trim() || sending) return;

    const optimistic: ChatMessage = {
      role: "user",
      content: content.trim(),
      ts: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimistic]);
    setInput("");
    setSending(true);
    setError(null);

    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN && sessionId) {
      ws.send(JSON.stringify({ content: content.trim(), confirm_booking: confirm }));
      return;
    }

    await sendViaRest(content.trim(), confirm);
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    void handleSend(input, false);
  }

  async function handleConfirm() {
    await handleSend("confirm", true);
  }

  async function startSession() {
    const token = await getAccessToken();
    if (!token) return;
    setSending(true);
    try {
      const session = await api.createChatSession(token);
      onSessionCreated(session.id);
      setMessages(session.messages ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not start chat");
    } finally {
      setSending(false);
    }
  }

  return (
    <section className="flex h-[min(520px,70vh)] flex-col rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-800">Booking assistant</h2>
        <span
          className={`rounded-full px-2 py-0.5 text-xs ${
            status === "live"
              ? "bg-emerald-100 text-emerald-800"
              : status === "connecting"
                ? "bg-amber-100 text-amber-800"
                : "bg-slate-100 text-slate-600"
          }`}
        >
          {status === "live" ? "Live" : status === "connecting" ? "Connecting…" : "REST"}
        </span>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {!sessionId && (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
            <p className="text-sm text-slate-600">
              Start a conversation to book with AI help.
            </p>
            <button
              type="button"
              onClick={startSession}
              disabled={sending}
              className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700"
            >
              Start chat
            </button>
          </div>
        )}
        {sessionId &&
          messages.map((m, i) => (
            <div
              key={`${m.ts ?? i}-${m.role}`}
              className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm ${
                  m.role === "user"
                    ? "bg-teal-600 text-white"
                    : "bg-slate-100 text-slate-800"
                }`}
              >
                {m.content}
              </div>
            </div>
          ))}
        <div ref={bottomRef} />
      </div>

      {error && <p className="px-4 pb-2 text-xs text-red-600">{error}</p>}

      {sessionId && (
        <form onSubmit={handleSubmit} className="border-t border-slate-100 p-4">
          <div className="flex gap-2">
            <input
              className="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm"
              placeholder="e.g. Book a cleaning next Tuesday at 2pm"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={sending}
            />
            <button
              type="submit"
              disabled={sending || !input.trim()}
              className="rounded-xl bg-teal-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              Send
            </button>
          </div>
          {canConfirm && (
            <button
              type="button"
              disabled={sending}
              onClick={() => void handleConfirm()}
              className="mt-2 w-full rounded-lg border border-teal-200 py-2 text-xs font-medium text-teal-700 hover:bg-teal-50"
            >
              Confirm booking from chat
            </button>
          )}
        </form>
      )}
    </section>
  );
}
