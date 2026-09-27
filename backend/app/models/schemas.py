"""
Pydantic models — request/response shapes for the API, plus the small
structured-output shape the LLM is asked to return for intent detection.
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


Intent = Literal["appointment", "general_information", "callback", "unknown"]


# ---------- LLM structured output ----------

class IntentResult(BaseModel):
    intent: Intent
    name: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    phone: Optional[str] = None
    reply: str = Field(..., description="What the voice assistant should say back to the caller")


# ---------- VAPI webhook ----------

class VapiWebhookPayload(BaseModel):
    """
    VAPI sends different 'message.type' payloads (status-update,
    transcript, end-of-call-report, etc). We only care about ones that
    carry a user utterance we need to respond to. Rather than model
    VAPI's entire schema, we accept the raw body as a dict in the route
    and pull out what we need — see routes/webhook.py.
    """
    pass


class WebhookResponse(BaseModel):
    """What we send back to VAPI so it can speak the reply."""
    reply: str


# ---------- Appointments ----------

class AppointmentCreate(BaseModel):
    name: str
    date: str
    time: str
    phone: Optional[str] = None
    call_id: Optional[str] = None


class AppointmentOut(AppointmentCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Callbacks ----------

class CallbackCreate(BaseModel):
    name: str
    phone: str
    call_id: Optional[str] = None


class CallbackOut(CallbackCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Calls ----------

class CallOut(BaseModel):
    id: int
    call_id: str
    phone: Optional[str] = None
    transcript: Optional[str] = None
    intent: Optional[str] = None
    assistant_response: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
