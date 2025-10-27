# app/routers/auth_multiuser.py
"""
Router de autenticación multiusuario con cuentas
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..db import get_db
from ..models import User, Account, AccountUser
from ..schemas import (
    LoginRequest, LoginResponse, RegisterRequest,
    UserOut, AccountOut
)
from ..auth_multiuser import (
    authenticate_user, get_password_hash, create_access_token,
    get_user_accounts, create_account_slug, ensure_unique_slug,
    get_current_user
)

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])

# ---------- REGISTRO ----------

@router.post("/register", response_model=LoginResponse)
async def register_user_with_account(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registrar nuevo usuario y crear su primera cuenta
    Este es el endpoint principal para nuevos anfitriones
    """
    # Verificar que el email no exista
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con este email"
        )
    
    try:
        # Crear usuario
        user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            password_hash=get_password_hash(user_data.password),
            phone=user_data.phone,
            is_active=True
        )
        
        db.add(user)
        db.flush()  # Para obtener el ID del usuario
        
        # Crear cuenta para el usuario
        base_slug = create_account_slug(user_data.account_name)
        unique_slug = ensure_unique_slug(db, base_slug)
        
        account = Account(
            name=user_data.account_name,
            slug=unique_slug,
            contact_email=user_data.email,
            phone=user_data.phone,
            trial_ends_at=datetime.now(timezone.utc) + timedelta(days=30)  # 30 días de trial
        )
        
        db.add(account)
        db.flush()  # Para obtener el ID de la cuenta
        
        # Crear membresía como owner
        membership = AccountUser(
            account_id=account.id,
            user_id=user.id,
            role="owner",
            invitation_accepted_at=datetime.now(timezone.utc)
        )
        
        db.add(membership)
        db.commit()
        
        # Refrescar objetos
        db.refresh(user)
        db.refresh(account)
        
        # Crear token de acceso
        access_token = create_access_token(data={"sub": user.id})
        
        # Preparar respuesta
        user_out = UserOut.from_orm(user)
        account_out = AccountOut.from_orm(account)
        account_out.apartments_count = 0
        account_out.users_count = 1
        
        return LoginResponse(
            access_token=access_token,
            user=user_out,
            accounts=[account_out],
            default_account_id=account.id
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando usuario y cuenta: {str(e)}"
        )

# ---------- LOGIN ----------

@router.post("/login", response_model=LoginResponse)
async def login_user(
    user_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login de usuario con lista de cuentas disponibles"""
    # Autenticar usuario
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Obtener cuentas del usuario
    accounts = get_user_accounts(db, user.id)
    
    if not accounts and not user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no pertenece a ninguna cuenta activa"
        )
    
    # Crear token de acceso
    access_token = create_access_token(data={"sub": user.id})
    
    # Preparar cuentas para respuesta
    accounts_out = []
    for account in accounts:
        account_out = AccountOut.from_orm(account)
        accounts_out.append(account_out)
    
    # Determinar cuenta por defecto (la primera o la más reciente)
    default_account_id = accounts[0].id if accounts else None
    
    return LoginResponse(
        access_token=access_token,
        user=UserOut.from_orm(user),
        accounts=accounts_out,
        default_account_id=default_account_id
    )

# ---------- LOGIN CON FORM (COMPATIBILIDAD) ----------

@router.post("/token", response_model=LoginResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login usando OAuth2PasswordRequestForm (compatibilidad con Swagger)"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Obtener cuentas del usuario
    accounts = get_user_accounts(db, user.id)
    
    # Crear token de acceso
    access_token = create_access_token(data={"sub": user.id})
    
    # Preparar cuentas para respuesta
    accounts_out = []
    for account in accounts:
        account_out = AccountOut.from_orm(account)
        accounts_out.append(account_out)
    
    default_account_id = accounts[0].id if accounts else None
    
    return LoginResponse(
        access_token=access_token,
        user=UserOut.from_orm(user),
        accounts=accounts_out,
        default_account_id=default_account_id
    )

# ---------- INFORMACIÓN DEL USUARIO ACTUAL ----------

@router.get("/me", response_model=LoginResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener información del usuario actual y sus cuentas"""
    # Obtener cuentas del usuario
    accounts = get_user_accounts(db, current_user.id)
    
    # Preparar cuentas para respuesta
    accounts_out = []
    for account in accounts:
        account_out = AccountOut.from_orm(account)
        accounts_out.append(account_out)
    
    default_account_id = accounts[0].id if accounts else None
    
    return LoginResponse(
        access_token="current",  # Token actual (no se regenera)
        user=UserOut.from_orm(current_user),
        accounts=accounts_out,
        default_account_id=default_account_id
    )

# ---------- CAMBIO DE CUENTA ----------

@router.post("/switch-account/{account_id}")
async def switch_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cambiar a una cuenta específica (verificar acceso)"""
    # Verificar que el usuario tenga acceso a la cuenta
    if not current_user.is_superadmin:
        user_accounts = get_user_accounts(db, current_user.id)
        if not any(acc.id == account_id for acc in user_accounts):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes acceso a esta cuenta"
            )
    
    # Verificar que la cuenta existe y está activa
    account = db.query(Account).filter(
        and_(Account.id == account_id, Account.is_active == True)
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada o inactiva"
        )
    
    return {
        "message": "Cuenta cambiada exitosamente",
        "account_id": account_id,
        "account_name": account.name,
        "instructions": "Usa el header 'X-Account-ID: {account_id}' en las próximas peticiones"
    }

# ---------- LOGOUT ----------

@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_user)
):
    """Logout del usuario (invalidar token del lado del cliente)"""
    return {
        "message": "Logout exitoso",
        "instructions": "Elimina el token del almacenamiento local del cliente"
    }

# ---------- REGISTRO RÁPIDO PARA DEMO ----------

@router.post("/quick-register")
async def quick_register(
    email: str = Form(...),
    full_name: str = Form(...),
    account_name: str = Form(...),
    password: str = Form(default="123456"),
    db: Session = Depends(get_db)
):
    """
    Registro rápido para demos (contraseña por defecto)
    ¡SOLO PARA DESARROLLO/DEMO!
    """
    # Verificar que el email no exista
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con este email"
        )
    
    try:
        # Crear usuario
        user = User(
            email=email,
            full_name=full_name,
            password_hash=get_password_hash(password),
            is_active=True
        )
        
        db.add(user)
        db.flush()
        
        # Crear cuenta
        base_slug = create_account_slug(account_name)
        unique_slug = ensure_unique_slug(db, base_slug)
        
        account = Account(
            name=account_name,
            slug=unique_slug,
            contact_email=email,
            trial_ends_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        
        db.add(account)
        db.flush()
        
        # Crear membresía
        membership = AccountUser(
            account_id=account.id,
            user_id=user.id,
            role="owner",
            invitation_accepted_at=datetime.now(timezone.utc)
        )
        
        db.add(membership)
        db.commit()
        
        return {
            "success": True,
            "message": f"Usuario {email} registrado exitosamente",
            "account_name": account_name,
            "account_id": account.id,
            "login_url": "/api/v1/auth/login",
            "credentials": {
                "email": email,
                "password": password
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en registro rápido: {str(e)}"
        )