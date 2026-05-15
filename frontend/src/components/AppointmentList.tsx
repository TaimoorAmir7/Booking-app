"use client";

import type { Appointment } from "@/types";

type Props = {
  appointments: Appointment[];
  loading?: boolean;
  onRefresh?: () => void;
};

function formatRange(starts: string, ends: string) {
  const s = new Date(starts);
  const e = new Date(ends);
  return `${s.toLocaleDateString()} ${s.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} – ${e.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
}

export function AppointmentList({ appointments, loading, onRefresh }: Props) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-800">Your appointments</h2>
        {onRefresh && (
          <button
            type="button"
            onClick={onRefresh}
            className="text-xs text-teal-600 hover:underline"
          >
            Refresh
          </button>
        )}
      </div>
      {loading && <p className="text-sm text-slate-500">Loading…</p>}
      {!loading && appointments.length === 0 && (
        <p className="text-sm text-slate-500">No appointments yet. Book via chat or the form.</p>
      )}
      <ul className="space-y-3">
        {appointments.map((a) => (
          <li
            key={a.id}
            className="rounded-xl border border-slate-100 bg-slate-50/80 px-4 py-3"
          >
            <p className="font-medium text-slate-900">{a.title}</p>
            <p className="mt-1 text-xs text-slate-600">{formatRange(a.starts_at, a.ends_at)}</p>
            <div className="mt-2 flex gap-2">
              <span className="rounded-full bg-teal-100 px-2 py-0.5 text-xs text-teal-800">
                {a.status}
              </span>
              <span className="rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-600">
                {a.source}
              </span>
            </div>
            {a.notes && <p className="mt-2 text-xs text-slate-500">{a.notes}</p>}
          </li>
        ))}
      </ul>
    </section>
  );
}
