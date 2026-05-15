"use client";

import { FormEvent, useState } from "react";
import type { ExtractedSlots } from "@/types";

type Props = {
  initialSlots?: ExtractedSlots | null;
  onSubmit: (data: {
    title: string;
    starts_at: string;
    ends_at: string;
    notes?: string;
  }) => Promise<void>;
  loading?: boolean;
};

function toLocalInput(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function BookingForm({ initialSlots, onSubmit, loading }: Props) {
  const [title, setTitle] = useState(initialSlots?.title ?? "");
  const [startsAt, setStartsAt] = useState(toLocalInput(initialSlots?.starts_at));
  const [endsAt, setEndsAt] = useState(toLocalInput(initialSlots?.ends_at));
  const [notes, setNotes] = useState(initialSlots?.notes ?? "");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!title.trim()) {
      setError("Title is required.");
      return;
    }
    const start = new Date(startsAt);
    const end = new Date(endsAt);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
      setError("Valid start and end times are required.");
      return;
    }
    if (end <= start) {
      setError("End time must be after start time.");
      return;
    }
    try {
      await onSubmit({
        title: title.trim(),
        starts_at: start.toISOString(),
        ends_at: end.toISOString(),
        notes: notes.trim() || undefined,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Booking failed");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h3 className="text-sm font-semibold text-slate-800">Book appointment</h3>
      <p className="text-xs text-slate-500">
        Use this form when chat details are incomplete or you prefer structured booking.
      </p>
      {error && (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      )}
      <label className="block text-sm">
        <span className="text-slate-600">Title</span>
        <input
          className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Consultation"
        />
      </label>
      <label className="block text-sm">
        <span className="text-slate-600">Starts</span>
        <input
          type="datetime-local"
          className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
          value={startsAt}
          onChange={(e) => setStartsAt(e.target.value)}
        />
      </label>
      <label className="block text-sm">
        <span className="text-slate-600">Ends</span>
        <input
          type="datetime-local"
          className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
          value={endsAt}
          onChange={(e) => setEndsAt(e.target.value)}
        />
      </label>
      <label className="block text-sm">
        <span className="text-slate-600">Notes</span>
        <textarea
          className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
          rows={2}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </label>
      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-lg bg-teal-600 py-2.5 text-sm font-medium text-white hover:bg-teal-700 disabled:opacity-60"
      >
        {loading ? "Saving…" : "Create appointment"}
      </button>
    </form>
  );
}
