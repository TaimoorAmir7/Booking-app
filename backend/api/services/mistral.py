import json
import logging
import re
from typing import Any

import httpx
from django.conf import settings

logger = logging.getLogger("api.ai")

EXTRACTION_PROMPT = """You help users book appointments. From the conversation, extract booking fields.
Return ONLY valid JSON with keys: title, starts_at, ends_at, notes, complete (boolean).
Use ISO 8601 UTC for starts_at/ends_at when known, else null.
Set complete=true only when title and both times are confidently known.
If ambiguous, set complete=false and leave missing fields null."""


def _fallback_extract(text: str) -> dict[str, Any]:
    """Rule-based fallback when Mistral is unavailable."""
    slots: dict[str, Any] = {
        "title": None,
        "starts_at": None,
        "ends_at": None,
        "notes": None,
        "complete": False,
    }
    lower = text.lower()
    if "consult" in lower or "checkup" in lower or "visit" in lower:
        slots["title"] = "Consultation"
    if re.search(r"\d{4}-\d{2}-\d{2}", text):
        slots["complete"] = False
    return slots


def _parse_json_content(content: str) -> dict[str, Any]:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.MULTILINE)
    return json.loads(content)


async def extract_appointment_slots(
    messages: list[dict[str, str]],
) -> tuple[dict[str, Any], str]:
    """
    Returns (slots, assistant_reply).
    Logs interactions for debugging.
    """
    if not settings.MISTRAL_API_KEY:
        logger.warning("[ai] MISTRAL_API_KEY missing — using fallback extractor")
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        slots = _fallback_extract(last_user)
        reply = (
            "I can help book an appointment. Please share title, date, start time, and duration "
            "or use the booking form if details are unclear."
        )
        if not slots.get("complete"):
            reply += " (AI key not configured — limited parsing.)"
        return slots, reply

    payload = {
        "model": settings.MISTRAL_MODEL,
        "messages": [
            {"role": "system", "content": EXTRACTION_PROMPT},
            *[{"role": m["role"], "content": m["content"]} for m in messages[-12:]],
        ],
        "temperature": 0.2,
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
        slots = _parse_json_content(content)
        reply = _slots_to_reply(slots)
        return slots, reply
    except Exception as exc:
        logger.exception("[ai] mistral call failed: %s", exc)
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        slots = _fallback_extract(last_user)
        return slots, (
            "I had trouble reaching the AI service. "
            "Please confirm your appointment details or use the booking form."
        )


def _slots_to_reply(slots: dict[str, Any]) -> str:
    if slots.get("complete"):
        return (
            f"Great — I have '{slots.get('title')}' from {slots.get('starts_at')} "
            f"to {slots.get('ends_at')}. Say 'confirm' to book or correct any detail."
        )
    missing = []
    if not slots.get("title"):
        missing.append("appointment type/title")
    if not slots.get("starts_at"):
        missing.append("start date and time")
    if not slots.get("ends_at"):
        missing.append("end time or duration")
    if missing:
        return f"I still need: {', '.join(missing)}. You can also use the booking form."
    return "Tell me more about when you'd like to meet."
