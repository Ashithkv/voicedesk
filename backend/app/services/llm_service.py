"""
Talks to the OpenAI API to do two things in a single call:

1. Classify the caller's intent into one of the four supported buckets.
2. Extract whatever slot data that intent needs (name/date/time for an
   appointment, name/phone for a callback), and draft the line the
   voice assistant should say back.

We use OpenAI's structured output (response_format=json_schema) so the
model is forced to return exactly the shape our IntentResult expects —
no regex-parsing of free text, no "hope it says JSON".
"""
import json
import logging
from openai import OpenAI

from app.config import settings
from app.models.schemas import IntentResult

logger = logging.getLogger("voicedesk.llm")

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Add it to backend/.env — see .env.example."
            )
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


SYSTEM_PROMPT = """You are the intent-understanding brain behind VoiceDesk, \
a small voice assistant that answers phone calls for a business.

For every caller message, classify it into exactly one intent:
- "appointment": the caller wants to book/schedule an appointment. Try to \
extract their name, preferred date, and preferred time from the \
conversation so far. If something is missing, set it to null and your \
reply should ask for just that missing piece.
- "callback": the caller wants someone to call them back later. Try to \
extract their name and phone number. If something is missing, ask for it.
- "general_information": the caller is asking a general question you can \
just answer directly (hours, services, pricing, location, etc). Answer it \
briefly and helpfully in `reply`.
- "unknown": the message doesn't clearly fit any of the above, is empty, \
or is too vague to act on. Politely ask the caller to clarify what they need.

Always fill in `reply` with a short, natural, spoken-friendly sentence — \
this text will be spoken aloud by the voice assistant, so keep it \
conversational and under ~30 words, no markdown, no lists.

Use conversation history to fill in slots gathered across multiple turns \
(e.g. caller gave their name in turn 1, date in turn 2)."""


INTENT_JSON_SCHEMA = {
    "name": "intent_result",
    "schema": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": ["appointment", "general_information", "callback", "unknown"],
            },
            "name": {"type": ["string", "null"]},
            "date": {"type": ["string", "null"]},
            "time": {"type": ["string", "null"]},
            "phone": {"type": ["string", "null"]},
            "reply": {"type": "string"},
        },
        "required": ["intent", "name", "date", "time", "phone", "reply"],
        "additionalProperties": False,
    },
    "strict": True,
}


def classify_and_respond(transcript: str, history: list[dict] | None = None) -> IntentResult:
    """
    transcript: the caller's latest message.
    history: optional prior turns as [{"role": "user"|"assistant", "content": "..."}]
             so multi-turn slot-filling (e.g. appointment booking across
             several sentences) works without extra state on our side —
             VAPI sends the running transcript with each webhook call.
    """
    client = get_client()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": transcript})

    completion = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        response_format={"type": "json_schema", "json_schema": INTENT_JSON_SCHEMA},
        temperature=0.3,
    )

    raw = completion.choices[0].message.content
    data = json.loads(raw)
    return IntentResult(**data)
