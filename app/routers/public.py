# app/routers/public.py
"""
Endpoints públicos para que los clientes gestionen sus apartamentos
"""
from __future__ import annotations
import os
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..db import get_db
from .. import models, schemas

# Initialize templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

router = APIRouter(prefix="/public", tags=["public"])

@router.get("/register", response_class=HTMLResponse)
def apartment_registration_page(request: Request):
    """Página pública para registrar apartamentos"""
    return templates.TemplateResponse("public_register.html", {"request": request})

@router.post("/register-apartment")
def register_apartment_public(
    code: str = Form(...),
    name: str = Form(...),
    owner_email: str = Form(...),
    owner_name: str = Form(None),
    phone: str = Form(None),
    db: Session = Depends(get_db)
):
    """Endpoint público para registrar apartamentos (sin autenticación)"""
    
    # Validaciones básicas
    code = code.upper().strip()
    if len(code) < 3:
        raise HTTPException(status_code=400, detail="El código debe tener al menos 3 caracteres")
    
    if len(name.strip()) < 3:
        raise HTTPException(status_code=400, detail="El nombre debe tener al menos 3 caracteres")
    
    # Verificar si ya existe
    existing = db.query(models.Apartment).filter(models.Apartment.code == code).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"El apartamento {code} ya está registrado")
    
    try:
        # Crear apartamento
        apt = models.Apartment(
            code=code,
            name=name.strip(),
            owner_email=owner_email.lower().strip(),
            is_active=True
        )
        db.add(apt)
        db.commit()
        db.refresh(apt)
        
        return {
            "success": True,
            "message": f"Apartamento {code} registrado exitosamente",
            "apartment": {
                "id": apt.id,
                "code": apt.code,
                "name": apt.name,
                "owner_email": apt.owner_email
            },
            "next_steps": [
                f"1. Busca el bot @UriApartment_Bot en Telegram",
                f"2. Envía /start para comenzar",
                f"3. Configura tu apartamento con: /usar {code}",
                f"4. ¡Envía fotos de facturas para procesamiento automático!",
                f"5. Ve tus gastos en: {os.getenv('API_BASE_URL', 'https://ses-gastos.onrender.com')}/api/v1/dashboard/"
            ]
        }
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"El apartamento {code} ya está registrado")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error registrando apartamento: {str(e)}")

@router.get("/apartments")
def list_public_apartments(db: Session = Depends(get_db)):
    """Listar apartamentos públicos (solo códigos activos)"""
    apartments = db.query(models.Apartment).filter(models.Apartment.is_active == True).all()
    return {
        "total": len(apartments),
        "apartments": [
            {
                "code": apt.code,
                "name": apt.name,
                "created_at": apt.created_at
            }
            for apt in apartments
        ]
    }

@router.get("/check/{code}")
def check_apartment_availability(code: str, db: Session = Depends(get_db)):
    """Verificar si un código de apartamento está disponible"""
    code = code.upper().strip()
    existing = db.query(models.Apartment).filter(models.Apartment.code == code).first()
    
    return {
        "code": code,
        "available": existing is None,
        "message": f"Código {code} {'disponible' if existing is None else 'ya está en uso'}"
    }