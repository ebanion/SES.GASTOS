# app/routers/apartments.py
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
import os

router = APIRouter(prefix="/api/v1/apartments", tags=["apartments"])

def _auth(
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
    key: str | None = Query(default=None),
):
    admin = os.getenv("ADMIN_KEY", "")
    provided = x_internal_key or key
    if not admin or provided != admin:
        raise HTTPException(status_code=403, detail="Forbidden")

@router.get("", response_model=list[schemas.ApartmentOut])
def list_apartments(db: Session = Depends(get_db)):
    rows = db.query(models.Apartment).order_by(models.Apartment.created_at.desc()).all()
    return [
        schemas.ApartmentOut(
            id=str(r.id),
            code=r.code,
            name=r.name,
            owner_email=r.owner_email,
            telegram_chat_id=None
        ) for r in rows
    ]

@router.post("", response_model=schemas.ApartmentOut)
def create_apartment(
    payload: schemas.ApartmentIn,
    db: Session = Depends(get_db),
    _: None = Depends(_auth),
):
    exists = db.query(models.Apartment).filter(models.Apartment.code == payload.code).first()
    if exists:
        raise HTTPException(status_code=409, detail="code_in_use")

    a = models.Apartment(
        code=payload.code,
        name=payload.name,
        owner_email=payload.owner_email,
    )
    db.add(a); db.commit(); db.refresh(a)
    return schemas.ApartmentOut(
        id=str(a.id),
        code=a.code,
        name=a.name,
        owner_email=a.owner_email,
        telegram_chat_id=None
    )
