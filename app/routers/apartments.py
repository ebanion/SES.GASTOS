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
    # 1) Evita 500 si ya existe el code
    existing = db.query(models.Apartment).filter(models.Apartment.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=409, detail="apartment_code_already_exists")

    apt = models.Apartment(
        code=payload.code.strip(),
        name=(payload.name or "").strip() or None,
        owner_email=(payload.owner_email or None),
        # is_active: default True en modelo/DB
    )
    try:
        db.add(apt)
        db.commit()
        db.refresh(apt)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="apartment_code_already_exists")
    except Exception as e:
        db.rollback()
        # Para depurar mejor en PROD, devolvemos 500 con tag
        raise HTTPException(status_code=500, detail=f"create_apartment_failed: {e}")

    return apt

@router.get("", response_model=list[schemas.ApartmentOut])
def list_apartments(db: Session = Depends(get_db)):
    q = db.query(models.Apartment).order_by(models.Apartment.created_at.desc())
    return q.all()

@router.get("/by_code/{code}", response_model=schemas.ApartmentOut)
def get_apartment_by_code(code: str, db: Session = Depends(get_db)):
    apt = db.query(models.Apartment).filter(models.Apartment.code == code).first()
    if not apt:
        raise HTTPException(status_code=404, detail="not_found")
    return apt

@router.get("/{apartment_id}", response_model=schemas.ApartmentOut)
def get_apartment(apartment_id: str, db: Session = Depends(get_db)):
    """Obtener apartamento por ID"""
    apt = db.query(models.Apartment).filter(models.Apartment.id == apartment_id).first()
    if not apt:
        raise HTTPException(status_code=404, detail="apartment_not_found")
    return apt

@router.patch("/{apartment_id}", response_model=schemas.ApartmentOut, dependencies=[Depends(require_internal_key)])
def update_apartment(apartment_id: str, updates: dict, db: Session = Depends(get_db)):
    """Actualizar apartamento (PATCH)"""
    apt = db.query(models.Apartment).filter(models.Apartment.id == apartment_id).first()
    if not apt:
        raise HTTPException(status_code=404, detail="apartment_not_found")
    
    # Campos permitidos para actualizar
    allowed_fields = {"name", "owner_email", "is_active"}
    
    for field, value in updates.items():
        if field in allowed_fields and hasattr(apt, field):
            setattr(apt, field, value)
    
    try:
        db.commit()
        db.refresh(apt)
        return apt
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"update_failed: {e}")

@router.delete("/{apartment_id}", dependencies=[Depends(require_internal_key)])
def delete_apartment(apartment_id: str, db: Session = Depends(get_db)):
    """Eliminar apartamento"""
    apt = db.query(models.Apartment).filter(models.Apartment.id == apartment_id).first()
    if not apt:
        raise HTTPException(status_code=404, detail="apartment_not_found")
    
    try:
        db.delete(apt)
        db.commit()
        return {"success": True, "message": f"Apartamento {apt.code} eliminado"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"delete_failed: {e}")

@router.post("/bulk", dependencies=[Depends(require_internal_key)])
def create_bulk_apartments(apartments: list[schemas.ApartmentCreate], db: Session = Depends(get_db)):
    """Crear múltiples apartamentos de una vez"""
    created_apartments = []
    errors = []
    
    for apt_data in apartments:
        try:
            # Verificar si ya existe
            existing = db.query(models.Apartment).filter(models.Apartment.code == apt_data.code).first()
            if existing:
                errors.append(f"Apartamento {apt_data.code} ya existe")
                continue
            
            apt = models.Apartment(
                code=apt_data.code,
                name=apt_data.name,
                owner_email=apt_data.owner_email,
                is_active=apt_data.is_active
            )
            db.add(apt)
            db.flush()  # Para obtener el ID
            created_apartments.append({
                "id": apt.id,
                "code": apt.code,
                "name": apt.name
            })
        except Exception as e:
            errors.append(f"Error creando {apt_data.code}: {str(e)}")
    
    try:
        db.commit()
        return {
            "success": True,
            "created": len(created_apartments),
            "apartments": created_apartments,
            "errors": errors
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"bulk_create_failed: {e}")



