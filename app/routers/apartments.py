# app/routers/apartments.py
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import os

from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/v1/apartments", tags=["apartments"])

def require_internal_key(
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key")
):
    if x_internal_key != os.getenv("ADMIN_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden")

@router.post("", response_model=schemas.ApartmentOut, dependencies=[Depends(require_internal_key)])
def create_apartment(payload: schemas.ApartmentCreate, db: Session = Depends(get_db)):
    apt = models.Apartment(
        code=payload.code.strip(),
        name=(payload.name or "").strip(),
        owner_email=(payload.owner_email or None),
        is_active=True,
    )
    try:
        db.add(apt)
        db.commit()
        db.refresh(apt)
        return apt
    except IntegrityError as e:
        # Si ya existe, devolvemos el existente (idempotente) en 200
        db.rollback()
        print(f"[apartments] IntegrityError on insert: {e}")
        existing = (
            db.query(models.Apartment)
            .filter(models.Apartment.code == payload.code.strip())
            .first()
        )
        if existing:
            return existing
        # Si por lo que sea no lo encontramos, sí devolvemos 409
        raise HTTPException(status_code=409, detail="apartment_code_already_exists")

@router.get("", response_model=list[schemas.ApartmentOut])
def list_apartments(db: Session = Depends(get_db)):
    return db.query(models.Apartment).order_by(models.Apartment.created_at.desc()).all()

