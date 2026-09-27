"""
Takes the LLM's IntentResult and performs the one small business action
each intent needs. Kept intentionally dumb: no retries, no external
calendar sync, no SMS confirmation — this is a portfolio project, not a
call center.
"""
import logging
from sqlalchemy.orm import Session

from app.database import Appointment, Callback
from app.models.schemas import IntentResult

logger = logging.getLogger("voicedesk.actions")


def handle_intent(db: Session, result: IntentResult, call_id: str, phone: str | None) -> str:
    """
    Persists a record when we have enough slot data, and returns the
    final reply text to speak. If required slots are missing, we don't
    save anything yet — the LLM's `reply` will already be asking for
    the missing piece, so we just pass it through.
    """
    if result.intent == "appointment":
        if result.name and result.date and result.time:
            appointment = Appointment(
                name=result.name,
                date=result.date,
                time=result.time,
                phone=phone or result.phone,
                call_id=call_id,
            )
            db.add(appointment)
            db.commit()
            logger.info("Saved appointment for %s on %s %s", result.name, result.date, result.time)
        return result.reply

    if result.intent == "callback":
        if result.name and (phone or result.phone):
            callback = Callback(
                name=result.name,
                phone=phone or result.phone,
                call_id=call_id,
            )
            db.add(callback)
            db.commit()
            logger.info("Saved callback request for %s", result.name)
        return result.reply

    # general_information and unknown both just speak the LLM's reply —
    # nothing to persist beyond the call log itself.
    return result.reply
