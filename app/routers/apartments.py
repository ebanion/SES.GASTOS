# app/routers/apartments.py
from __future__ import annotations

import os
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/v1/apartments", tags=["apartments"])


# --- Guard de clave interna (ADMIN_KEY) ---
def require_internal_key(
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
):
    if x_internal_key != os.getenv("ADMIN_KEY"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


# --- Crear apartment ---
@router.post(
    "",
    response_model=schemas.ApartmentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_internal_key)],
)
def create_apartment(payload: schemas.ApartmentCreate, db: Session = Depends(get_db)):
    code = payload.code.strip()
    name = payload.name.strip()
    if not code or not name:
        raise HTTPException(status_code=422, detail="code and name are required")

    # Evitar 500 si ya existe (carrera controlada con try/except)
    exists = db.query(models.Apartment).filter(models.Apartment.code == code).first()
    if exists:
        raise HTTPException(status_code=409, detail="apartment_code_already_exists")

    apt = models.Apartment(
        code=code,
        name=name,
        owner_email=(payload.owner_email or None),
    )
    try:
        db.add(apt)
        db.commit()
        db.refresh(apt)
    except IntegrityError:
        db.rollback()
        # por si otra request metió el mismo code en paralelo
        raise HTTPException(status_code=409, detail="apartment_code_already_exists")

    return apt


# --- Listar apartments (opcional: solo activos) ---
@router.get("", response_model=list[schemas.ApartmentOut])
def list_apartments(only_active: bool = False, db: Session = Depends(get_db)):
    q = db.query(models.Apartment)
    if only_active:
        q = q.filter(models.Apartment.is_active.is_(True))
    return q.order_by(models.Apartment.created_at.desc()).all()


# --- Obtener un apartment ---
@router.get("/{apartment_id}", response_model=schemas.ApartmentOut)
def get_apartment(apartment_id: UUID, db: Session = Depends(get_db)):
    apt = db.query(models.Apartment).get(apartment_id)
    if not apt:
        raise HTTPException(status_code=404, detail="not_found")
    return apt


# --- Actualizar (parcial) un apartment ---
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
    apt = db.query(models.Apartment).get(apartment_id)
    if not apt:
        raise HTTPException(status_code=404, detail="not_found")

    # Cambios opcionales
    if payload.name is not None:
        new_name = payload.name.strip()
        if not new_name:
            raise HTTPException(status_code=422, detail="name cannot be empty")
        apt.name = new_name

    if payload.owner_email is not None:
        apt.owner_email = payload.owner_email

    if payload.is_active is not None:
        apt.is_active = payload.is_active

    # Cambio de code (garantizando unicidad)
    if payload.code is not None:
        new_code = payload.code.strip()
        if not new_code:
            raise HTTPException(status_code=422, detail="code cannot be empty")
        if new_code != apt.code:
            clash = (
                db.query(models.Apartment)
                .filter(models.Apartment.code == new_code)
                .first()
            )
            if clash:
                raise HTTPException(status_code=409, detail="apartment_code_already_exists")
            apt.code = new_code

    try:
        db.commit()
        db.refresh(apt)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="apartment_code_already_exists")

    return apt