import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any

import httpx
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger("api.ai")

ASSISTANT_NAME = "Taimoor"

EXTRACTION_PROMPT = f"""You are {ASSISTANT_NAME}'s appointment booking assistant.

Personality and rules:
- You ONLY help book appointments for {ASSISTANT_NAME}. Nothing else.
- If the user asks unrelated questions (weather, jokes, general knowledge, coding, etc.), politely decline:
  say you are {ASSISTANT_NAME}'s assistant and can only help schedule appointments. Set off_topic=true.
- Use the FULL conversation history. If the user already said the appointment type earlier, keep it in title.
- Never expose raw JSON, ISO timestamps, or technical formats in reply.
- Ask ONE short, friendly question at a time for the next missing detail.
- If the user says "tomorrow", "next Monday", etc., resolve dates in starts_at/ends_at internally but in reply use natural words like "tomorrow" or "Monday".
- If start time is known but no end time, assume a 30-minute appointment.
- When complete=true, briefly confirm type, date, and time in plain English and invite them to confirm booking.

Return ONLY valid JSON:
{{
  "title": string or null,
  "starts_at": ISO-8601 UTC or null,
  "ends_at": ISO-8601 UTC or null,
  "notes": string or null,
  "complete": boolean,
  "off_topic": boolean,
  "reply": "natural conversational message to the user"
}}"""

BOOKING_HINTS = re.compile(
    r"\b(book|booking|appointment|schedule|consult|checkup|check-up|visit|cleaning|"
    r"dental|doctor|tomorrow|today|monday|tuesday|wednesday|thursday|friday|"
    r"saturday|sunday|am|pm|morning|afternoon|confirm)\b",
    re.I,
)

OFF_TOPIC_HINTS = re.compile(
    r"\b(weather|joke|news|politics|football|soccer|bitcoin|stock|recipe|"
    r"who are you|what is the meaning|write me a|poem|homework|python code)\b",
    re.I,
)

TITLE_HINTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(cleaning|teeth)\b", re.I), "Dental cleaning"),
    (re.compile(r"\b(checkup|check-up)\b", re.I), "Checkup"),
    (re.compile(r"\b(consult)\b", re.I), "Consultation"),
    (re.compile(r"\b(dental)\b", re.I), "Dental appointment"),
    (re.compile(r"\b(doctor|physician)\b", re.I), "Doctor visit"),
]


def _user_messages(messages: list[dict[str, str]]) -> list[str]:
    return [m["content"] for m in messages if m.get("role") == "user"]


def _merge_user_text(messages: list[dict[str, str]]) -> str:
    return " ".join(_user_messages(messages)).lower()


def _title_from_history(messages: list[dict[str, str]]) -> str | None:
    for text in reversed(_user_messages(messages)):
        for pattern, label in TITLE_HINTS:
            if pattern.search(text):
                return label
    return None


def _parse_time_on_date(base_date, text: str) -> datetime | None:
    lower = text.lower()
    hour = None
    minute = 0
    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", lower)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2) or 0)
        ampm = m.group(3)
        if ampm == "pm" and hour < 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0
        if not ampm and hour <= 7:
            hour += 12
    elif "morning" in lower:
        hour, minute = 9, 0
    elif "afternoon" in lower:
        hour, minute = 14, 0
    elif "evening" in lower:
        hour, minute = 17, 0
    if hour is None:
        return None
    return timezone.make_aware(
        datetime(base_date.year, base_date.month, base_date.day, hour, minute),
        timezone.get_current_timezone(),
    )


def _resolve_date(text: str):
    today = timezone.localdate()
    lower = text.lower()
    if "tomorrow" in lower:
        return today + timedelta(days=1)
    if "today" in lower:
        return today
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i, name in enumerate(weekdays):
        if name in lower:
            days_ahead = (i - today.weekday()) % 7
            if days_ahead == 0 and "next" in lower:
                days_ahead = 7
            return today + timedelta(days=days_ahead)
    return None


def _fallback_extract(messages: list[dict[str, str]]) -> dict[str, Any]:
    merged = _merge_user_text(messages)
    last = _user_messages(messages)[-1] if messages else ""

    slots: dict[str, Any] = {
        "title": _title_from_history(messages),
        "starts_at": None,
        "ends_at": None,
        "notes": None,
        "complete": False,
        "off_topic": False,
    }

    target_date = _resolve_date(merged)
    if target_date:
        start_dt = _parse_time_on_date(target_date, merged) or _parse_time_on_date(
            target_date, last
        )
        if start_dt:
            end_dt = start_dt + timedelta(minutes=30)
            slots["starts_at"] = start_dt.isoformat()
            slots["ends_at"] = end_dt.isoformat()

    if slots["title"] and slots["starts_at"] and slots["ends_at"]:
        slots["complete"] = True

    return slots


def _fallback_reply(messages: list[dict[str, str]], slots: dict[str, Any]) -> str:
    merged = _merge_user_text(messages)
    last = _user_messages(messages)[-1] if messages else ""

    if OFF_TOPIC_HINTS.search(last) and not BOOKING_HINTS.search(merged):
        return (
            f"Hi — I'm {ASSISTANT_NAME}'s appointment assistant. "
            f"I can only help you book an appointment with {ASSISTANT_NAME}. "
            "What type of visit would you like to schedule?"
        )

    if slots.get("complete"):
        title = slots.get("title") or "your appointment"
        when = "tomorrow" if "tomorrow" in merged else "on the date you chose"
        if "today" in merged:
            when = "today"
        return (
            f"Perfect — I'll book {title} {when} at the time we discussed. "
            "Tap **Confirm booking from chat** when you're ready."
        )

    if not slots.get("title"):
        return "Happy to help. What type of appointment would you like to book?"

    if not slots.get("starts_at"):
        if "tomorrow" in merged or "tomorrow" in last.lower():
            return f"Got it — a {slots['title']} tomorrow. What time works best for you?"
        if _resolve_date(merged):
            return f"Sure — for your {slots['title']}, what time should I put down?"
        return f"For your {slots['title']}, which date would you like?"

    return "Almost there — does a 30-minute slot work, or do you need a different end time?"


def _clean_slots(raw: dict[str, Any]) -> tuple[dict[str, Any], str, bool]:
    reply = str(raw.pop("reply", "") or "").strip()
    off_topic = bool(raw.pop("off_topic", False))
    slots = {
        "title": raw.get("title"),
        "starts_at": raw.get("starts_at"),
        "ends_at": raw.get("ends_at"),
        "notes": raw.get("notes"),
        "complete": bool(raw.get("complete")),
    }
    if off_topic:
        slots["complete"] = False
    if not reply:
        reply = _slots_to_reply(slots)
    return slots, reply, off_topic


def _parse_json_content(content: str) -> dict[str, Any]:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.MULTILINE)
    return json.loads(content)


async def extract_appointment_slots(
    messages: list[dict[str, str]],
) -> tuple[dict[str, Any], str]:
    if not settings.MISTRAL_API_KEY:
        logger.warning("[ai] MISTRAL_API_KEY missing — using fallback extractor")
        slots = _fallback_extract(messages)
        return slots, _fallback_reply(messages, slots)

    payload = {
        "model": settings.MISTRAL_MODEL,
        "messages": [
            {"role": "system", "content": EXTRACTION_PROMPT},
            *[{"role": m["role"], "content": m["content"]} for m in messages[-12:]],
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.MISTRAL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            res.raise_for_status()
            data = res.json()
        content = data["choices"][0]["message"]["content"]
        logger.info("[ai] mistral response model=%s", settings.MISTRAL_MODEL)
        raw = _parse_json_content(content)
        slots, reply, off_topic = _clean_slots(dict(raw))
        if off_topic:
            reply = (
                f"I'm {ASSISTANT_NAME}'s appointment assistant — I can only help with "
                f"booking appointments. What would you like to schedule?"
            )
        return slots, reply
    except Exception as exc:
        logger.exception("[ai] mistral call failed: %s", exc)
        slots = _fallback_extract(messages)
        return slots, _fallback_reply(messages, slots)


def _slots_to_reply(slots: dict[str, Any]) -> str:
    if slots.get("complete"):
        title = slots.get("title") or "your appointment"
        return (
            f"Great — I have {title} reserved for the time we discussed. "
            "Say **confirm** or use the button to book."
        )
    if not slots.get("title"):
        return "What type of appointment should I book for you?"
    if not slots.get("starts_at"):
        return "Which date and time work best for you?"
    if not slots.get("ends_at"):
        return "What time should it end, or is 30 minutes okay?"
    return "Tell me a bit more about when you'd like to come in."
