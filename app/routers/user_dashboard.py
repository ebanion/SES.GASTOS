# app/routers/user_dashboard.py
"""
Dashboard personalizado para usuarios autenticados
"""
from __future__ import annotations
import os
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..db import get_db
from .. import models, schemas
from ..auth import get_current_active_user

# Initialize templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

router = APIRouter(prefix="/dashboard", tags=["user_dashboard"])

@router.get("/", response_class=HTMLResponse)
def user_dashboard(
    request: Request,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Dashboard principal del usuario"""
    # Obtener apartamentos del usuario
    apartments = db.query(models.Apartment).filter(
        models.Apartment.user_id == current_user.id,
        models.Apartment.is_active == True
    ).all()
    
    # Estadísticas básicas
    total_apartments = len(apartments)
    
    # Obtener gastos recientes
    recent_expenses = []
    if apartments:
        apartment_ids = [apt.id for apt in apartments]
        recent_expenses = db.query(models.Expense).filter(
            models.Expense.apartment_id.in_(apartment_ids)
        ).order_by(models.Expense.created_at.desc()).limit(10).all()
    
    return templates.TemplateResponse("user_dashboard.html", {
        "request": request,
        "user": current_user,
        "apartments": apartments,
        "total_apartments": total_apartments,
        "recent_expenses": recent_expenses
    })

@router.get("/apartments", response_class=HTMLResponse)
def manage_apartments(
    request: Request,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Gestión de apartamentos del usuario"""
    apartments = db.query(models.Apartment).filter(
        models.Apartment.user_id == current_user.id
    ).all()
    
    return templates.TemplateResponse("user_apartments.html", {
        "request": request,
        "user": current_user,
        "apartments": apartments
    })

@router.post("/apartments/create")
def create_apartment(
    code: str = Form(...),
    name: str = Form(...),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crear nuevo apartamento para el usuario"""
    
    # Validaciones
    code = code.upper().strip()
    name = name.strip()
    
    if len(code) < 3:
        raise HTTPException(status_code=400, detail="El código debe tener al menos 3 caracteres")
    
    if len(name) < 3:
        raise HTTPException(status_code=400, detail="El nombre debe tener al menos 3 caracteres")
    
    # Verificar si el código ya existe
    existing = db.query(models.Apartment).filter(models.Apartment.code == code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"El código {code} ya está en uso")
    
    try:
        # Crear apartamento
        apartment = models.Apartment(
            code=code,
            name=name,
            owner_email=current_user.email,
            user_id=current_user.id,
            is_active=True
        )
        db.add(apartment)
        db.commit()
        db.refresh(apartment)
        
        return {
            "success": True,
            "message": f"Apartamento {code} creado exitosamente",
            "apartment": {
                "id": apartment.id,
                "code": apartment.code,
                "name": apartment.name
            },
            "bot_instructions": [
                f"1. Busca @UriApartment_Bot en Telegram",
                f"2. Envía /start para comenzar",
                f"3. Configura tu apartamento con: /usar {code}",
                f"4. ¡Envía fotos de facturas para procesamiento automático!"
            ]
        }
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"El código {code} ya está en uso")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creando apartamento: {str(e)}")

@router.patch("/apartments/{apartment_id}")
def update_apartment(
    apartment_id: str,
    name: str = Form(None),
    is_active: bool = Form(None),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualizar apartamento del usuario"""
    
    # Verificar que el apartamento pertenece al usuario
    apartment = db.query(models.Apartment).filter(
        models.Apartment.id == apartment_id,
        models.Apartment.user_id == current_user.id
    ).first()
    
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    
    try:
        # Actualizar campos
        if name is not None:
            apartment.name = name.strip()
        if is_active is not None:
            apartment.is_active = is_active
        
        db.commit()
        db.refresh(apartment)
        
        return {
            "success": True,
            "message": "Apartamento actualizado exitosamente",
            "apartment": {
                "id": apartment.id,
                "code": apartment.code,
                "name": apartment.name,
                "is_active": apartment.is_active
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error actualizando apartamento: {str(e)}")

@router.delete("/apartments/{apartment_id}")
def delete_apartment(
    apartment_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Eliminar apartamento del usuario"""
    
    # Verificar que el apartamento pertenece al usuario
    apartment = db.query(models.Apartment).filter(
        models.Apartment.id == apartment_id,
        models.Apartment.user_id == current_user.id
    ).first()
    
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    
    try:
        apartment_code = apartment.code
        db.delete(apartment)
        db.commit()
        
        return {
            "success": True,
            "message": f"Apartamento {apartment_code} eliminado exitosamente"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error eliminando apartamento: {str(e)}")

@router.get("/profile", response_class=HTMLResponse)
def user_profile(
    request: Request,
    current_user: models.User = Depends(get_current_active_user)
):
    """Perfil del usuario"""
    return templates.TemplateResponse("user_profile.html", {
        "request": request,
        "user": current_user
    })

@router.post("/profile/update")
def update_profile(
    full_name: str = Form(...),
    phone: str = Form(None),
    company: str = Form(None),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualizar perfil del usuario"""
    
    try:
        current_user.full_name = full_name.strip()
        current_user.phone = phone.strip() if phone else None
        current_user.company = company.strip() if company else None
        
        db.commit()
        
        return {
            "success": True,
            "message": "Perfil actualizado exitosamente"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error actualizando perfil: {str(e)}")