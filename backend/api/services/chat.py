from datetime import datetime, timezone as dt_timezone
from typing import Any

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from api.models import Appointment, AppointmentStatus, ChatSession, User
from api.services.mistral import extract_appointment_slots


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    dt = parse_datetime(value)
    if dt and timezone.is_naive(dt):
        dt = timezone.make_aware(dt, dt_timezone.utc)
    return dt


async def process_chat_message(
    session: ChatSession,
    user: User,
    content: str,
    *,
    confirm_booking: bool = False,
) -> dict[str, Any]:
    session.append_message("user", content)
    history = [{"role": m["role"], "content": m["content"]} for m in session.messages]

    slots, assistant_reply = await extract_appointment_slots(history)
    session.metadata = {
        **session.metadata,
        "extracted_slots": slots,
        "model": session.metadata.get("model"),
    }

    appointment_created = None
    needs_form = not slots.get("complete")

    if confirm_booking and slots.get("complete"):
        starts = _parse_dt(slots.get("starts_at"))
        ends = _parse_dt(slots.get("ends_at"))
        if starts and ends and ends > starts:
            appt = await Appointment.objects.acreate(
                user=user,
                business=user.business,
                title=slots.get("title") or "Appointment",
                starts_at=starts,
                ends_at=ends,
                notes=slots.get("notes"),
                status=AppointmentStatus.SCHEDULED,
                source="chat_ai",
            )
            appointment_created = str(appt.id)
            assistant_reply = f"Booked! Your appointment id is {appt.id}."
            needs_form = False
        else:
            assistant_reply = "Times look invalid. Please use the form or clarify start/end."
            needs_form = True

    session.append_message("assistant", assistant_reply)
    await session.asave(update_fields=["messages", "metadata", "last_message_at", "updated_at"])

    return {
        "session_id": str(session.id),
        "reply": assistant_reply,
        "slots": slots,
        "needs_form": needs_form,
        "appointment_id": appointment_created,
        "messages": session.messages,
    }
