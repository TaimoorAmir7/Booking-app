export type User = {
  id: string;
  email: string;
  full_name: string;
  business_id: string | null;
  created_at: string;
};

export type Tokens = {
  access: string;
  refresh: string;
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  ts?: string;
};

export type ExtractedSlots = {
  title?: string | null;
  starts_at?: string | null;
  ends_at?: string | null;
  notes?: string | null;
  complete?: boolean;
};

export type Appointment = {
  id: string;
  title: string;
  starts_at: string;
  ends_at: string;
  status: string;
  notes?: string | null;
  source: string;
  created_at: string;
  updated_at: string;
};

export type ChatSession = {
  id: string;
  title: string | null;
  messages: ChatMessage[];
  metadata: Record<string, unknown>;
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ChatReply = {
  session_id: string;
  reply: string;
  slots: ExtractedSlots;
  needs_form: boolean;
  appointment_id: string | null;
  messages: ChatMessage[];
};
