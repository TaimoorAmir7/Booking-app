"use client";

type Period = "AM" | "PM";

export type DateTimeParts = {
  date: string;
  hour: string;
  minute: string;
  period: Period;
};

const HOURS = Array.from({ length: 12 }, (_, i) => String(i + 1));
const MINUTES = ["00", "15", "30", "45"];

export function emptyParts(): DateTimeParts {
  return { date: "", hour: "9", minute: "00", period: "AM" };
}

export function isoToParts(iso: string | null | undefined): DateTimeParts {
  if (!iso) return emptyParts();
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return emptyParts();
  const pad = (n: number) => String(n).padStart(2, "0");
  let h = d.getHours();
  const period: Period = h >= 12 ? "PM" : "AM";
  h = h % 12 || 12;
  return {
    date: `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`,
    hour: String(h),
    minute: pad(d.getMinutes()),
    period,
  };
}

export function partsToIso(parts: DateTimeParts): string | null {
  if (!parts.date || !parts.hour) return null;
  let h = parseInt(parts.hour, 10);
  if (Number.isNaN(h) || h < 1 || h > 12) return null;
  const m = parseInt(parts.minute, 10) || 0;
  if (parts.period === "PM" && h !== 12) h += 12;
  if (parts.period === "AM" && h === 12) h = 0;
  const iso = `${parts.date}T${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:00`;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString();
}

export function addMinutesToParts(parts: DateTimeParts, minutes: number): DateTimeParts {
  const iso = partsToIso(parts);
  if (!iso) return parts;
  const d = new Date(iso);
  d.setMinutes(d.getMinutes() + minutes);
  return isoToParts(d.toISOString());
}

type Props = {
  label: string;
  value: DateTimeParts;
  onChange: (value: DateTimeParts) => void;
  minDate?: string;
};

export function DateTimePicker({ label, value, onChange, minDate }: Props) {
  const set = (patch: Partial<DateTimeParts>) => onChange({ ...value, ...patch });

  return (
    <div className="space-y-2">
      <span className="text-sm text-slate-600">{label}</span>
      <input
        type="date"
        className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
        value={value.date}
        min={minDate}
        onChange={(e) => set({ date: e.target.value })}
      />
      <div className="grid grid-cols-3 gap-2">
        <select
          className="rounded-lg border border-slate-200 px-2 py-2 text-sm"
          value={value.hour}
          onChange={(e) => set({ hour: e.target.value })}
          aria-label={`${label} hour`}
        >
          {HOURS.map((h) => (
            <option key={h} value={h}>
              {h}
            </option>
          ))}
        </select>
        <select
          className="rounded-lg border border-slate-200 px-2 py-2 text-sm"
          value={value.minute}
          onChange={(e) => set({ minute: e.target.value })}
          aria-label={`${label} minute`}
        >
          {MINUTES.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
        <select
          className="rounded-lg border border-slate-200 px-2 py-2 text-sm"
          value={value.period}
          onChange={(e) => set({ period: e.target.value as Period })}
          aria-label={`${label} AM or PM`}
        >
          <option value="AM">AM</option>
          <option value="PM">PM</option>
        </select>
      </div>
    </div>
  );
}
