import type {
  Appointment,
  ChatReply,
  ChatSession,
  Tokens,
  User,
} from "@/types";

function isLocalNextDev(): boolean {
  if (typeof window === "undefined") return false;
  return window.location.hostname === "localhost" && window.location.port === "3000";
}

function apiBaseUrl(): string {
  const env = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (env) return env.replace(/\/$/, "");
  // `npm run dev` on :3000 — Django/Daphne runs on :4000
  if (isLocalNextDev()) return "http://localhost:4000/api";
  if (typeof window !== "undefined") return `${window.location.origin}/api`;
  return "http://localhost:4000/api";
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function fieldErrors(obj: Record<string, unknown>): string[] {
  const parts: string[] = [];
  for (const [key, val] of Object.entries(obj)) {
    if (key === "detail" && typeof val === "string") {
      parts.push(val);
    } else if (Array.isArray(val)) {
      parts.push(`${key}: ${val.map(String).join(", ")}`);
    } else if (typeof val === "string") {
      parts.push(`${key}: ${val}`);
    }
  }
  return parts;
}

function parseError(data: unknown): string {
  if (!data || typeof data !== "object") return "Request failed";
  const record = data as Record<string, unknown>;

  if (typeof record.error === "string") return record.error;

  if (typeof record.error === "object" && record.error !== null) {
    const parts = fieldErrors(record.error as Record<string, unknown>);
    if (parts.length) return parts.join("; ");
  }

  const direct = fieldErrors(record);
  if (direct.length) return direct.join("; ");

  return "Request failed";
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${apiBaseUrl()}${path}`, { ...options, headers });
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const message = parseError(data);
    let text = message;
    if (message === "Request failed") {
      if (res.status === 404) {
        text = isLocalNextDev()
          ? "API not found. Start the backend: daphne on port 4000."
          : `API not found (404). Check NEXT_PUBLIC_API_URL.`;
      } else {
        text = `Error ${res.status}`;
      }
    }
    throw new ApiError(text, res.status);
  }
  return data as T;
}

export const api = {
  signup(body: { email: string; password: string; full_name: string }) {
    return request<{ user: User; tokens: Tokens }>("/auth/signup/", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  login(body: { email: string; password: string }) {
    return request<{ user: User; tokens: Tokens }>("/auth/login/", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  refresh(refresh: string) {
    return request<{ access: string }>("/auth/refresh/", {
      method: "POST",
      body: JSON.stringify({ refresh }),
    });
  },

  me(token: string) {
    return request<User>("/auth/me/", {}, token);
  },

  listAppointments(token: string) {
    return request<Appointment[]>("/appointments/", {}, token);
  },

  createAppointment(
    token: string,
    body: {
      title: string;
      starts_at: string;
      ends_at: string;
      notes?: string;
      status?: string;
    }
  ) {
    return request<Appointment>("/appointments/", {
      method: "POST",
      body: JSON.stringify(body),
    }, token);
  },

  listChatSessions(token: string) {
    return request<ChatSession[]>("/chat/sessions/", {}, token);
  },

  createChatSession(token: string, title?: string) {
    return request<ChatSession>("/chat/sessions/", {
      method: "POST",
      body: JSON.stringify({ title: title ?? "Booking chat" }),
    }, token);
  },

  sendChatMessage(
    token: string,
    body: { content: string; session_id?: string; confirm_booking?: boolean }
  ) {
    return request<ChatReply>("/chat/messages/", {
      method: "POST",
      body: JSON.stringify(body),
    }, token);
  },
};

export function getWsUrl(sessionId: string, accessToken: string): string {
  const env = process.env.NEXT_PUBLIC_WS_URL?.trim();
  let base = env;
  if (!base && typeof window !== "undefined") {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    base = `${proto}://${window.location.host}`;
  }
  if (!base) base = "ws://localhost:4000";
  return `${base.replace(/\/$/, "")}/ws/chat/${sessionId}/?token=${encodeURIComponent(accessToken)}`;
}
