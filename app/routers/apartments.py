# app/routers/apartments.py
import os
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/v1/apartments", tags=["apartments"])

def require_internal_key(
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key")
):
    if x_internal_key != os.getenv("ADMIN_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden")

@router.post(
    "",
    response_model=schemas.ApartmentOut,
    dependencies=[Depends(require_internal_key)],
)
def create_apartment(payload: schemas.ApartmentCreate, db: Session = Depends(get_db)):
    # Evitar 500 si el code ya existe
    existing = db.query(models.Apartment).filter(models.Apartment.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=409, detail="apartment_code_already_exists")

    apt = models.Apartment(
        code=payload.code.strip(),
        name=(payload.name or "").strip() or None,
        owner_email=payload.owner_email,
    )
    try:
        db.add(apt)
        db.commit()
        db.refresh(apt)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="apartment_code_already_exists")

    return apt

@router.get("", response_model=list[schemas.ApartmentOut])
def list_apartments(db: Session = Depends(get_db)):
    q = db.query(models.Apartment).order_by(models.Apartment.created_at.desc())
    return q.all()

@router.patch(
    "/{apartment_id}",
    response_model=schemas.ApartmentOut,
    dependencies=[Depends(require_internal_key)],
)
def update_apartment(
    apartment_id: UUID,
    payload: schemas.ApartmentUpdate,
    db: Session = Depends(get_db),
):
    apt = db.query(models.Apartment).filter(models.Apartment.id == apartment_id).first()
    if not apt:
        raise HTTPException(status_code=404, detail="not_found")

    if payload.name is not None:
        apt.name = (payload.name or "").strip() or None
    if payload.owner_email is not None:
        apt.owner_email = payload.owner_email
    if payload.is_active is not None:
        apt.is_active = payload.is_active

    db.commit()
    db.refresh(apt)
    return apt
