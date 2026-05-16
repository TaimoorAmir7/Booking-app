"use client";

import { FormEvent, useEffect, useState } from "react";
import type { ExtractedSlots } from "@/types";
import {
  DateTimePicker,
  addMinutesToParts,
  emptyParts,
  isoToParts,
  partsToIso,
  type DateTimeParts,
} from "@/components/DateTimePicker";

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

function todayIsoDate(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function BookingForm({ initialSlots, onSubmit, loading }: Props) {
  const [title, setTitle] = useState(initialSlots?.title ?? "");
  const [start, setStart] = useState<DateTimeParts>(() =>
    isoToParts(initialSlots?.starts_at)
  );
  const [end, setEnd] = useState<DateTimeParts>(() =>
    initialSlots?.ends_at
      ? isoToParts(initialSlots.ends_at)
      : addMinutesToParts(isoToParts(initialSlots?.starts_at), 30)
  );
  const [notes, setNotes] = useState(initialSlots?.notes ?? "");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialSlots?.title) setTitle(initialSlots.title);
    if (initialSlots?.starts_at) {
      const s = isoToParts(initialSlots.starts_at);
      setStart(s);
      setEnd(
        initialSlots.ends_at
          ? isoToParts(initialSlots.ends_at)
          : addMinutesToParts(s, 30)
      );
    }
    if (initialSlots?.notes) setNotes(initialSlots.notes);
  }, [initialSlots]);

  function handleStartChange(next: DateTimeParts) {
    setStart(next);
    if (partsToIso(next)) {
      setEnd(addMinutesToParts(next, 30));
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!title.trim()) {
      setError("Please choose an appointment type.");
      return;
    }
    const starts_at = partsToIso(start);
    const ends_at = partsToIso(end);
    if (!starts_at || !ends_at) {
      setError("Please pick a date and time for start and end.");
      return;
    }
    if (new Date(ends_at) <= new Date(starts_at)) {
      setError("End time must be after start time.");
      return;
    }
    try {
      await onSubmit({
        title: title.trim(),
        starts_at,
        ends_at,
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
        Pick a date from the calendar, then choose a time with AM or PM.
      </p>
      {error && (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      )}
      <label className="block text-sm">
        <span className="text-slate-600">Appointment type</span>
        <input
          className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Consultation, checkup, cleaning…"
        />
      </label>
      <DateTimePicker
        label="Start"
        value={start.date ? start : { ...emptyParts(), date: todayIsoDate() }}
        onChange={handleStartChange}
        minDate={todayIsoDate()}
      />
      <DateTimePicker
        label="End"
        value={end}
        onChange={setEnd}
        minDate={start.date || todayIsoDate()}
      />
      <label className="block text-sm">
        <span className="text-slate-600">Notes (optional)</span>
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
