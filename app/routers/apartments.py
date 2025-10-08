# app/routers/apartments.py
from __future__ import annotations

import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/v1/apartments", tags=["apartments"])


def require_internal_key(
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key")
):
    admin = os.getenv("ADMIN_KEY", "")
    if not admin or x_internal_key != admin:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post(
    "",
    response_model=schemas.ApartmentOut,
    dependencies=[Depends(require_internal_key)],
)
def create_apartment(payload: schemas.ApartmentCreate, db: Session = Depends(get_db)):
    # normaliza strings opcionales sin romper si vienen None
    code = (payload.code or "").strip()
    name = (payload.name or "").strip() or None
    owner_email = payload.owner_email or None

    if not code:
        raise HTTPException(status_code=422, detail="code_required")

    # evita 500 si ya existe
    existing = db.query(models.Apartment).filter(models.Apartment.code == code).first()
    if existing:
        raise HTTPException(status_code=409, detail="apartment_code_already_exists")

    apt = models.Apartment(
        code=code,
        name=name,
        owner_email=owner_email,
        # evita NOT NULL en esquemas antiguos sin default
        created_at=datetime.now(timezone.utc),
        is_active=True,
    )

    try:
        db.add(apt)
        db.commit()
        db.refresh(apt)
    except IntegrityError:
        db.rollback()
        # carrera o unique en DB
        raise HTTPException(status_code=409, detail="apartment_code_already_exists")
    except Exception as e:
        db.rollback()
        # log amable para ver el motivo real durante estos tests
        raise HTTPException(status_code=500, detail=f"create_failed: {e!s}")

    return apt


@router.get("", response_model=list[schemas.ApartmentOut])
def list_apartments(db: Session = Depends(get_db)):
    return (
        db.query(models.Apartment)
        .order_by(models.Apartment.created_at.desc())
        .all()
    )


@router.get("/by_code/{code}", response_model=schemas.ApartmentOut)
def get_by_code(code: str, db: Session = Depends(get_db)):
    apt = db.query(models.Apartment).filter(models.Apartment.code == code).first()
    if not apt:
        raise HTTPException(status_code=404, detail="not_found")
    return apt



