"""
POST /webhook/vapi

The single entry point VAPI calls during a live phone call. See
app/services/vapi_service.py for a full explanation of the event types
and how the dashboard needs to be configured for this to fire.
"""
import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db, Call
from app.services import vapi_service, llm_service, action_service

logger = logging.getLogger("voicedesk.webhook")
router = APIRouter()


@router.post("/webhook/vapi")
async def vapi_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    message_type = vapi_service.extract_message_type(payload)
    call_id = vapi_service.extract_call_id(payload)
    phone = vapi_service.extract_phone(payload)

    logger.info("VAPI event received: type=%s call_id=%s", message_type, call_id)

    if message_type == "function-call":
        transcript = vapi_service.extract_function_call_text(payload)
        history = vapi_service.extract_conversation_history(payload)

        result = llm_service.classify_and_respond(transcript, history)
        reply = action_service.handle_intent(db, result, call_id, phone)

        call_log = Call(
            call_id=call_id,
            phone=phone,
            transcript=transcript,
            intent=result.intent,
            assistant_response=reply,
        )
        db.add(call_log)
        db.commit()

        # This is the shape VAPI expects back from a function-call event:
        # the `result` string is what the assistant speaks next.
        return {"result": reply}

    if message_type == "end-of-call-report":
        summary = vapi_service.extract_end_of_call_summary(payload)
        call_log = Call(
            call_id=call_id,
            phone=phone,
            transcript=summary.get("transcript"),
            intent=None,
            assistant_response=f"Call ended: {summary.get('ended_reason')}",
        )
        db.add(call_log)
        db.commit()
        return {"status": "logged"}

    # status-update, speech-update, transcript (interim), hang, etc.
    # We don't need to act on these for VoiceDesk's small scope, but we
    # acknowledge them with 200 OK so VAPI doesn't retry/flag them.
    return {"status": "received", "type": message_type}
