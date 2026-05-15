"use client";

import { useCallback, useEffect, useState } from "react";
import { AppointmentList } from "@/components/AppointmentList";
import { BookingForm } from "@/components/BookingForm";
import { ChatPanel } from "@/components/ChatPanel";
import { Header } from "@/components/Header";
import { RequireAuth } from "@/components/RequireAuth";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Appointment, ExtractedSlots } from "@/types";

export default function DashboardPage() {
  const { getAccessToken } = useAuth();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loadingAppts, setLoadingAppts] = useState(true);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [slots, setSlots] = useState<ExtractedSlots | null>(null);
  const [showForm, setShowForm] = useState(true);

  const loadAppointments = useCallback(async () => {
    const token = await getAccessToken();
    if (!token) return;
    setLoadingAppts(true);
    try {
      const list = await api.listAppointments(token);
      setAppointments(list);
    } finally {
      setLoadingAppts(false);
    }
  }, [getAccessToken]);

  useEffect(() => {
    void loadAppointments();
  }, [loadAppointments]);

  const handleSlotsUpdate = useCallback((next: ExtractedSlots, needsForm: boolean) => {
    setSlots(next);
    setShowForm(needsForm || !next.complete);
  }, []);

  async function handleFormBooking(data: {
    title: string;
    starts_at: string;
    ends_at: string;
    notes?: string;
  }) {
    const token = await getAccessToken();
    if (!token) return;
    setBookingLoading(true);
    try {
      await api.createAppointment(token, data);
      await loadAppointments();
    } finally {
      setBookingLoading(false);
    }
  }

  return (
    <RequireAuth>
      <div className="min-h-screen bg-slate-50">
        <Header />
        <main className="mx-auto grid max-w-6xl gap-6 px-4 py-8 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <ChatPanel
              sessionId={sessionId}
              onSessionCreated={setSessionId}
              onSlotsUpdate={handleSlotsUpdate}
              onAppointmentBooked={loadAppointments}
            />
          </div>
          <div className="space-y-6">
            {showForm && (
              <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <BookingForm
                  initialSlots={slots}
                  onSubmit={handleFormBooking}
                  loading={bookingLoading}
                />
              </section>
            )}
            {!showForm && slots?.complete && (
              <p className="rounded-xl border border-teal-100 bg-teal-50 px-4 py-3 text-sm text-teal-800">
                Chat captured your booking details. Confirm in chat or edit via form.
                <button
                  type="button"
                  className="ml-2 underline"
                  onClick={() => setShowForm(true)}
                >
                  Show form
                </button>
              </p>
            )}
            <AppointmentList
              appointments={appointments}
              loading={loadingAppts}
              onRefresh={() => void loadAppointments()}
            />
          </div>
        </main>
      </div>
    </RequireAuth>
  );
}
