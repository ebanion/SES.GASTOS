# app/routers/apartments.py
from __future__ import annotations

import os
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, func

from ..db import get_db
from .. import models, schemas
from ..auth_multiuser import (
    get_current_user, get_current_account, require_member_or_above,
    require_admin_or_owner, require_superadmin, filter_apartments_by_account
)

router = APIRouter(prefix="/api/v1/apartments", tags=["apartments"])

# Legacy function para compatibilidad con APIs existentes
def require_internal_key(
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
    key: str | None = Query(default=None),
):
    admin = os.getenv("ADMIN_KEY", "")
    provided = x_internal_key or key
    if not admin or provided != admin:
        raise HTTPException(status_code=403, detail="Forbidden")

# ---------- NUEVOS ENDPOINTS CON CUENTAS ----------

@router.post("/", response_model=schemas.ApartmentOut)
def create_apartment_in_account(
    payload: schemas.ApartmentCreate, 
    current_account: models.Account = Depends(get_current_account),
    membership: models.AccountUser = Depends(require_admin_or_owner),
    db: Session = Depends(get_db)
):
    """Crear apartamento en la cuenta actual"""
    # Verificar que el código no exista en la cuenta
    existing = db.query(models.Apartment).filter(
        and_(
            models.Apartment.code == payload.code,
            models.Apartment.account_id == current_account.id
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="apartment_code_already_exists_in_account")

    # Verificar límite de apartamentos
    current_count = db.query(func.count(models.Apartment.id)).filter(
        models.Apartment.account_id == current_account.id
    ).scalar()
    
    if current_count >= current_account.max_apartments:
        raise HTTPException(
            status_code=400, 
            detail=f"Límite de apartamentos alcanzado ({current_account.max_apartments})"
        )

    apt = models.Apartment(
        code=payload.code.strip(),
        name=(payload.name or "").strip() or None,
        owner_email=(payload.owner_email or None),
        account_id=current_account.id,  # VINCULACIÓN CON CUENTA
        description=getattr(payload, 'description', None),
        address=getattr(payload, 'address', None),
        max_guests=getattr(payload, 'max_guests', None),
        bedrooms=getattr(payload, 'bedrooms', None),
        bathrooms=getattr(payload, 'bathrooms', None)
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
        raise HTTPException(status_code=500, detail=f"create_apartment_failed: {e}")

    return apt

# ---------- LEGACY ENDPOINT (MANTENER COMPATIBILIDAD) ----------

@router.post("", response_model=schemas.ApartmentOut, dependencies=[Depends(require_internal_key)])
def create_apartment_legacy(payload: schemas.ApartmentCreate, db: Session = Depends(get_db)):
    """LEGACY: Crear apartamento sin cuenta (solo para superadmin)"""
    # Para compatibilidad, crear apartamento sin cuenta
    # NOTA: Esto debería migrar a crear en una cuenta por defecto
    
    existing = db.query(models.Apartment).filter(models.Apartment.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=409, detail="apartment_code_already_exists")

    # Buscar cuenta por defecto o crear una
    default_account = db.query(models.Account).filter(models.Account.slug == "sistema").first()
    if not default_account:
        from ..auth_multiuser import create_account_slug, ensure_unique_slug
        default_account = models.Account(
            name="Sistema",
            slug="sistema",
            description="Cuenta por defecto para apartamentos legacy",
            max_apartments=1000
        )
        db.add(default_account)
        db.flush()

    apt = models.Apartment(
        code=payload.code.strip(),
        name=(payload.name or "").strip() or None,
        owner_email=(payload.owner_email or None),
        account_id=default_account.id,  # Asignar a cuenta por defecto
        # Mantener campo legacy para compatibilidad
        user_id=None
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
        raise HTTPException(status_code=500, detail=f"create_apartment_failed: {e}")

    return apt

# ---------- LISTAR APARTAMENTOS ----------

@router.get("/", response_model=List[schemas.ApartmentOut])
def list_apartments_in_account(
    current_account: models.Account = Depends(get_current_account),
    membership: models.AccountUser = Depends(require_member_or_above),
    db: Session = Depends(get_db),
    active_only: bool = Query(True, description="Solo apartamentos activos")
):
    """Listar apartamentos de la cuenta actual"""
    query = db.query(models.Apartment).filter(
        models.Apartment.account_id == current_account.id
    )
    
    if active_only:
        query = query.filter(models.Apartment.is_active == True)
    
    query = query.order_by(models.Apartment.created_at.desc())
    return query.all()

# ---------- LEGACY ENDPOINT ----------

@router.get("", response_model=list[schemas.ApartmentOut])
def list_apartments_legacy(db: Session = Depends(get_db)):
    """LEGACY: Listar todos los apartamentos (solo para compatibilidad)"""
    q = db.query(models.Apartment).order_by(models.Apartment.created_at.desc())
    return q.all()

# ---------- OBTENER APARTAMENTO ----------

@router.get("/id/{apartment_id}", response_model=schemas.ApartmentOut)
def get_apartment_by_id_in_account(
    apartment_id: str,
    current_account: models.Account = Depends(get_current_account),
    membership: models.AccountUser = Depends(require_member_or_above),
    db: Session = Depends(get_db)
):
    """Obtener apartamento por ID dentro de la cuenta"""
    apt = db.query(models.Apartment).filter(
        and_(
            models.Apartment.id == apartment_id,
            models.Apartment.account_id == current_account.id
        )
    ).first()
    
    if not apt:
        raise HTTPException(status_code=404, detail="apartment_not_found")
    return apt

@router.get("/code/{code}", response_model=schemas.ApartmentOut)
def get_apartment_by_code_in_account(
    code: str,
    current_account: models.Account = Depends(get_current_account),
    membership: models.AccountUser = Depends(require_member_or_above),
    db: Session = Depends(get_db)
):
    """Obtener apartamento por código dentro de la cuenta"""
    apt = db.query(models.Apartment).filter(
        and_(
            models.Apartment.code == code,
            models.Apartment.account_id == current_account.id
        )
    ).first()
    
    if not apt:
        raise HTTPException(status_code=404, detail="apartment_not_found")
    return apt

# ---------- LEGACY ENDPOINTS ----------

@router.get("/by_code/{code}", response_model=schemas.ApartmentOut)
def get_apartment_by_code_legacy(code: str, db: Session = Depends(get_db)):
    """LEGACY: Buscar apartamento por código globalmente"""
    apt = db.query(models.Apartment).filter(models.Apartment.code == code).first()
    if not apt:
        raise HTTPException(status_code=404, detail="not_found")
    return apt

@router.get("/{apartment_id}", response_model=schemas.ApartmentOut)
def get_apartment_legacy(apartment_id: str, db: Session = Depends(get_db)):
    """LEGACY: Obtener apartamento por ID globalmente"""
    apt = db.query(models.Apartment).filter(models.Apartment.id == apartment_id).first()
    if not apt:
        raise HTTPException(status_code=404, detail="apartment_not_found")
    return apt

# ---------- ACTUALIZAR APARTAMENTO ----------

@router.patch("/id/{apartment_id}", response_model=schemas.ApartmentOut)
def update_apartment_in_account(
    apartment_id: str, 
    updates: dict,
    current_account: models.Account = Depends(get_current_account),
    membership: models.AccountUser = Depends(require_admin_or_owner),
    db: Session = Depends(get_db)
):
    """Actualizar apartamento dentro de la cuenta"""
    apt = db.query(models.Apartment).filter(
        and_(
            models.Apartment.id == apartment_id,
            models.Apartment.account_id == current_account.id
        )
    ).first()
    
    if not apt:
        raise HTTPException(status_code=404, detail="apartment_not_found")
    
    # Campos permitidos para actualizar
    allowed_fields = {
        "name", "description", "address", "max_guests", 
        "bedrooms", "bathrooms", "is_active", "owner_email"
    }
    
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

# ---------- LEGACY ENDPOINT ----------

@router.patch("/{apartment_id}", response_model=schemas.ApartmentOut, dependencies=[Depends(require_internal_key)])
def update_apartment_legacy(apartment_id: str, updates: dict, db: Session = Depends(get_db)):
    """LEGACY: Actualizar apartamento globalmente"""
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

# ---------- ELIMINAR APARTAMENTO ----------

@router.delete("/id/{apartment_id}")
def delete_apartment_in_account(
    apartment_id: str,
    current_account: models.Account = Depends(get_current_account),
    membership: models.AccountUser = Depends(require_admin_or_owner),
    db: Session = Depends(get_db)
):
    """Eliminar apartamento de la cuenta"""
    apt = db.query(models.Apartment).filter(
        and_(
            models.Apartment.id == apartment_id,
            models.Apartment.account_id == current_account.id
        )
    ).first()
    
    if not apt:
        raise HTTPException(status_code=404, detail="apartment_not_found")
    
    # Verificar si tiene gastos o ingresos asociados
    expenses_count = db.query(func.count(models.Expense.id)).filter(
        models.Expense.apartment_id == apartment_id
    ).scalar()
    
    incomes_count = db.query(func.count(models.Income.id)).filter(
        models.Income.apartment_id == apartment_id
    ).scalar()
    
    if expenses_count > 0 or incomes_count > 0:
        # No eliminar, solo desactivar
        apt.is_active = False
        db.commit()
        return {
            "success": True, 
            "message": f"Apartamento {apt.code} desactivado (tiene {expenses_count} gastos y {incomes_count} ingresos)",
            "action": "deactivated"
        }
    
    try:
        db.delete(apt)
        db.commit()
        return {"success": True, "message": f"Apartamento {apt.code} eliminado", "action": "deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"delete_failed: {e}")

# ---------- LEGACY ENDPOINT ----------

@router.delete("/{apartment_id}", dependencies=[Depends(require_internal_key)])
def delete_apartment_legacy(apartment_id: str, db: Session = Depends(get_db)):
    """LEGACY: Eliminar apartamento globalmente"""
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



