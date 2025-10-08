# app/routers/apartments.py
from __future__ import annotations

import os
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/v1/apartments", tags=["apartments"])

def require_internal_key(
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
    key: str | None = Query(default=None),
):
    admin = os.getenv("ADMIN_KEY", "")
    provided = x_internal_key or key
    if not admin or provided != admin:
        raise HTTPException(status_code=403, detail="Forbidden")

@router.post("", response_model=schemas.ApartmentOut, dependencies=[Depends(require_internal_key)])
def create_apartment(payload: schemas.ApartmentCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Apartment).filter(models.Apartment.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=409, detail="apartment_code_already_exists")

    apt = models.Apartment(
        code=payload.code.strip(),
        name=(payload.name or "").strip() or None,
        owner_email=payload.owner_email,
    )
    try:
        db.add(apt); db.commit(); db.refresh(apt)
    except IntegrityError:
        db.rollback()
        # si la carrera fue por code duplicado, devolvemos 409
        raise HTTPException(status_code=409, detail="apartment_code_already_exists")
    except Exception:
        db.rollback()
        # cualquier otra restricción antigua se reporta limpio
        raise HTTPException(status_code=500, detail="integrity_error")

    return apt

@router.get("", response_model=list[schemas.ApartmentOut])
def list_apartments(db: Session = Depends(get_db)):
    return db.query(models.Apartment).order_by(models.Apartment.created_at.desc()).all()

@router.get("/by_code/{code}", response_model=schemas.ApartmentOut)
def get_apartment_by_code(code: str, db: Session = Depends(get_db)):
    apt = db.query(models.Apartment).filter(models.Apartment.code == code).first()
    if not apt:
        raise HTTPException(status_code=404, detail="not_found")
    return apt

@router.patch("/{apartment_id}", response_model=schemas.ApartmentOut, dependencies=[Depends(require_internal_key)])
def update_apartment(apartment_id: str, payload: schemas.ApartmentUpdate, db: Session = Depends(get_db)):
    apt = db.query(models.Apartment).filter(models.Apartment.id == apartment_id).first()
    if not apt:
        raise HTTPException(status_code=404, detail="not_found")

    if payload.name is not None:
        apt.name = payload.name
    if payload.owner_email is not None:
        apt.owner_email = payload.owner_email
    if payload.is_active is not None:
        apt.is_active = payload.is_active

    db.commit(); db.refresh(apt)
    return apt


