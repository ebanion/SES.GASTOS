# app/auth_multiuser.py
"""
Sistema de autenticación multiusuario con cuentas (tenants)
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from .db import get_db
from .models import User, Account, AccountUser, Apartment
from .schemas import UserOut, AccountOut, LoginResponse

# Configuración
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 días

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# ---------- UTILIDADES DE CONTRASEÑA ----------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashear contraseña"""
    return pwd_context.hash(password)

# ---------- UTILIDADES DE TOKEN ----------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crear token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodificar token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ---------- UTILIDADES DE CUENTA ----------
def create_account_slug(name: str) -> str:
    """Crear slug único para la cuenta"""
    # Convertir a minúsculas y reemplazar espacios/caracteres especiales
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
    slug = re.sub(r'[\s-]+', '-', slug).strip('-')
    
    # Limitar longitud
    if len(slug) > 50:
        slug = slug[:50].rstrip('-')
    
    return slug or "cuenta"

def ensure_unique_slug(db: Session, base_slug: str) -> str:
    """Asegurar que el slug sea único"""
    slug = base_slug
    counter = 1
    
    while db.query(Account).filter(Account.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug

# ---------- AUTENTICACIÓN ----------
def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Autenticar usuario por email y contraseña"""
    user = db.query(User).filter(
        and_(User.email == email, User.is_active == True)
    ).first()
    
    if not user or not verify_password(password, user.password_hash):
        return None
    
    # Actualizar último login
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    return user

def get_user_accounts(db: Session, user_id: str) -> List[Account]:
    """Obtener todas las cuentas de un usuario"""
    accounts = db.query(Account).join(AccountUser).filter(
        and_(
            AccountUser.user_id == user_id,
            AccountUser.is_active == True,
            Account.is_active == True
        )
    ).all()
    
    return accounts

def get_user_role_in_account(db: Session, user_id: str, account_id: str) -> Optional[str]:
    """Obtener el rol del usuario en una cuenta específica"""
    membership = db.query(AccountUser).filter(
        and_(
            AccountUser.user_id == user_id,
            AccountUser.account_id == account_id,
            AccountUser.is_active == True
        )
    ).first()
    
    return membership.role if membership else None

def can_user_access_account(db: Session, user_id: str, account_id: str) -> bool:
    """Verificar si el usuario puede acceder a una cuenta"""
    # Superadministradores pueden acceder a todo
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.is_superadmin:
        return True
    
    # Verificar membresía activa
    membership = db.query(AccountUser).filter(
        and_(
            AccountUser.user_id == user_id,
            AccountUser.account_id == account_id,
            AccountUser.is_active == True
        )
    ).first()
    
    return membership is not None

# ---------- DEPENDENCIAS DE FASTAPI ----------
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Obtener usuario actual desde el token"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(
        and_(User.id == user_id, User.is_active == True)
    ).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_account(
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Account:
    """Obtener cuenta actual desde el header X-Account-ID"""
    if not x_account_id:
        # Si no se especifica cuenta, usar la primera disponible
        accounts = get_user_accounts(db, current_user.id)
        if not accounts:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario no pertenece a ninguna cuenta"
            )
        account = accounts[0]
    else:
        # Verificar que el usuario puede acceder a la cuenta especificada
        if not can_user_access_account(db, current_user.id, x_account_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes acceso a esta cuenta"
            )
        
        account = db.query(Account).filter(
            and_(Account.id == x_account_id, Account.is_active == True)
        ).first()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cuenta no encontrada"
            )
    
    return account

async def require_account_role(
    required_roles: List[str],
    current_user: User = Depends(get_current_user),
    current_account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
) -> AccountUser:
    """Verificar que el usuario tenga uno de los roles requeridos en la cuenta"""
    # Superadministradores pueden hacer todo
    if current_user.is_superadmin:
        # Crear membresía ficticia para superadmin
        class SuperAdminMembership:
            role = "superadmin"
            account_id = current_account.id
            user_id = current_user.id
        return SuperAdminMembership()
    
    membership = db.query(AccountUser).filter(
        and_(
            AccountUser.user_id == current_user.id,
            AccountUser.account_id == current_account.id,
            AccountUser.is_active == True
        )
    ).first()
    
    if not membership or membership.role not in required_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Se requiere uno de estos roles: {', '.join(required_roles)}"
        )
    
    return membership

# Dependencias específicas por rol
async def require_owner(
    current_user: User = Depends(get_current_user),
    current_account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
) -> AccountUser:
    """Requiere rol de owner"""
    return await require_account_role(["owner"], current_user, current_account, db)

async def require_admin_or_owner(
    current_user: User = Depends(get_current_user),
    current_account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
) -> AccountUser:
    """Requiere rol de admin o owner"""
    return await require_account_role(["owner", "admin"], current_user, current_account, db)

async def require_member_or_above(
    current_user: User = Depends(get_current_user),
    current_account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
) -> AccountUser:
    """Requiere rol de member o superior"""
    return await require_account_role(["owner", "admin", "member"], current_user, current_account, db)

# ---------- SUPERADMINISTRADOR ----------
async def require_superadmin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Requiere ser superadministrador del sistema"""
    if not current_user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de superadministrador"
        )
    return current_user

# ---------- UTILIDADES DE FILTRADO ----------
def filter_apartments_by_account(query, account_id: str):
    """Filtrar apartamentos por cuenta"""
    return query.filter(Apartment.account_id == account_id)

def get_account_apartments(db: Session, account_id: str) -> List[Apartment]:
    """Obtener todos los apartamentos de una cuenta"""
    return db.query(Apartment).filter(
        and_(
            Apartment.account_id == account_id,
            Apartment.is_active == True
        )
    ).all()