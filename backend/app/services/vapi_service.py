"""
Helpers for talking to VAPI.ai's webhook protocol.

VAPI sends a POST to your assistant's "Server URL" for several event
types (message.type): "status-update", "transcript", "speech-update",
"hang", "end-of-call-report", and — the one VoiceDesk actually acts on —
"function-call".

How the voice flow is wired (see README "VAPI integration" section for
the exact dashboard steps):

  1. The VAPI assistant is configured with one Function/Tool, e.g.
     `handleRequest(message: string)`.
  2. VAPI's own LLM (or ours, if you switch the assistant to "Custom
     LLM" mode) decides to call that function whenever the caller says
     something that needs a real action or answer.
  3. VAPI POSTs `{"message": {"type": "function-call", "functionCall": ...}}`
     to /webhook/vapi.
  4. We classify intent, run the matching business action (save an
     appointment/callback, or just answer), and return
     `{"result": "<text to speak>"}`.
  5. VAPI speaks `result` back to the caller over the phone line
     (Twilio carries the audio if you've connected a Twilio number in
     the VAPI dashboard — see README "Twilio integration").

We also log every "end-of-call-report" event so the dashboard has a
full transcript + final detected intent per call, without needing a
call to succeed every single turn to still show up in `GET /calls`.
"""
from typing import Any


def extract_message_type(payload: dict[str, Any]) -> str:
    return payload.get("message", {}).get("type", "unknown")


def extract_call_id(payload: dict[str, Any]) -> str:
    message = payload.get("message", {})
    call = message.get("call") or payload.get("call") or {}
    return call.get("id", "unknown-call")


def extract_phone(payload: dict[str, Any]) -> str | None:
    message = payload.get("message", {})
    call = message.get("call") or payload.get("call") or {}
    customer = call.get("customer") or {}
    return customer.get("number")


def extract_function_call_text(payload: dict[str, Any]) -> str:
    """
    Pull the caller's utterance out of a `function-call` event.
    VAPI puts the function's declared parameters under
    message.functionCall.parameters — VoiceDesk's function is declared
    with a single `message` string parameter (see README for the exact
    JSON schema to paste into the VAPI dashboard).
    """
    message = payload.get("message", {})
    function_call = message.get("functionCall", {})
    params = function_call.get("parameters", {}) or {}
    return params.get("message", "")


def extract_conversation_history(payload: dict[str, Any]) -> list[dict[str, str]]:
    """
    VAPI includes the running conversation (message.artifact.messages or
    message.messages, depending on API version) on most event types.
    We convert whatever's there into the plain [{role, content}] shape
    our llm_service expects, skipping system/tool entries.
    """
    message = payload.get("message", {})
    raw_messages = message.get("artifact", {}).get("messages") or message.get("messages") or []
    history = []
    for m in raw_messages:
        role = m.get("role")
        content = m.get("message") or m.get("content")
        if role in ("user", "assistant") and content:
            history.append({"role": role, "content": content})
    return history


def extract_end_of_call_summary(payload: dict[str, Any]) -> dict[str, Any]:
    message = payload.get("message", {})
    return {
        "transcript": message.get("transcript") or message.get("artifact", {}).get("transcript"),
        "ended_reason": message.get("endedReason"),
    }
