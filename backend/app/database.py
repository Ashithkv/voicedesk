"""
SQLite database setup using SQLAlchemy's ORM.

Three tables, matching the spec exactly: calls, appointments, callbacks.
Kept deliberately flat — no migrations framework, no multi-tenant ids,
no unnecessary indexes. create_all() is enough for a project this size.
"""
from datetime import datetime, timezone

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def utcnow():
    return datetime.now(timezone.utc)


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String, index=True, nullable=False)
    phone = Column(String, nullable=True)
    transcript = Column(Text, nullable=True)
    intent = Column(String, nullable=True)
    assistant_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    date = Column(String, nullable=False)   # kept as string (e.g. "2026-10-02") — no timezone/calendar logic needed for a portfolio demo
    time = Column(String, nullable=False)   # e.g. "3:30 PM"
    phone = Column(String, nullable=True)
    call_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class Callback(Base):
    __tablename__ = "callbacks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    call_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
