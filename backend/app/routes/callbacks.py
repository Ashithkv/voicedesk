from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db, Callback
from app.models.schemas import CallbackCreate, CallbackOut

router = APIRouter()


@router.post("/callbacks", response_model=CallbackOut)
def create_callback(payload: CallbackCreate, db: Session = Depends(get_db)):
    callback = Callback(**payload.model_dump())
    db.add(callback)
    db.commit()
    db.refresh(callback)
    return callback


@router.get("/callbacks", response_model=List[CallbackOut])
def list_callbacks(db: Session = Depends(get_db)):
    return db.query(Callback).order_by(Callback.created_at.desc()).all()
