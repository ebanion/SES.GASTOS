# app/routers/auth.py
"""
Router de autenticación y gestión de usuarios
"""
from __future__ import annotations
import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..db import get_db
from .. import models, schemas
from ..auth import (
    authenticate_user, create_access_token, get_password_hash,
    get_current_user_optional, get_current_active_user
)

# Initialize templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/", response_class=HTMLResponse)
def auth_page(request: Request, user: models.User = Depends(get_current_user_optional)):
    """Página principal de autenticación"""
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("auth_main.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user: models.User = Depends(get_current_user_optional)):
    """Página de login"""
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("auth_login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, user: models.User = Depends(get_current_user_optional)):
    """Página de registro"""
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("auth_register.html", {"request": request})

@router.post("/login")
def login(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Procesar login"""
    user = authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )
    
    # Actualizar último login
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    # Crear token
    access_token = create_access_token(data={"sub": user.email})
    
    # Establecer cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=30 * 24 * 60 * 60,  # 30 días
        samesite="lax"
    )
    
    return {
        "success": True,
        "message": f"Bienvenido, {user.full_name}!",
        "redirect": "/dashboard"
    }

@router.post("/register")
def register(
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    phone: str = Form(None),
    company: str = Form(None),
    db: Session = Depends(get_db)
):
    """Procesar registro"""
    
    # Validaciones
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
    
    if len(password.encode('utf-8')) > 72:
        raise HTTPException(status_code=400, detail="La contraseña es demasiado larga. Máximo 72 caracteres.")
    
    # Verificar si el usuario ya existe
    existing_user = db.query(models.User).filter(models.User.email == email.lower()).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Este email ya está registrado")
    
    try:
        # Crear usuario
        user = models.User(
            email=email.lower().strip(),
            full_name=full_name.strip(),
            password_hash=get_password_hash(password),
            phone=phone.strip() if phone else None,
            company=company.strip() if company else None,
            is_active=True,
            is_admin=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return {
            "success": True,
            "message": f"¡Cuenta creada exitosamente! Bienvenido, {user.full_name}",
            "redirect": "/auth/login"
        }
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Este email ya está registrado")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creando cuenta: {str(e)}")

@router.post("/logout")
def logout(response: Response):
    """Cerrar sesión"""
    response.delete_cookie(key="access_token")
    return {"success": True, "message": "Sesión cerrada", "redirect": "/auth/login"}

@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_active_user)):
    """Obtener información del usuario actual"""
    return current_user

@router.get("/check")
def check_auth(user: models.User = Depends(get_current_user_optional)):
    """Verificar estado de autenticación"""
    if user:
        return {
            "authenticated": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_admin": user.is_admin
            }
        }
    return {"authenticated": False}