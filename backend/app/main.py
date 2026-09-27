import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routes import webhook, appointments, callbacks, calls

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

app = FastAPI(
    title="VoiceDesk API",
    description="Small AI voice assistant backend — VAPI webhook, intent detection, and call/appointment/callback storage.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(webhook.router, tags=["webhook"])
app.include_router(appointments.router, tags=["appointments"])
app.include_router(callbacks.router, tags=["callbacks"])
app.include_router(calls.router, tags=["calls"])
