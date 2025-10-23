# app/auth.py
"""
Sistema de autenticación para SES.GASTOS
"""
from __future__ import annotations
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .db import get_db
from . import models

# Configuración
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 días

# Contexto de hash de contraseñas con manejo de errores
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except Exception as e:
    print(f"[AUTH] Warning: bcrypt setup issue: {e}")
    # Fallback más simple
    pwd_context = CryptContext(schemes=["bcrypt"])
security = HTTPBearer(auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"[AUTH] Error verifying with passlib, trying bcrypt directly: {e}")
        # Fallback usando bcrypt directamente
        try:
            import bcrypt
            password_bytes = plain_password.encode('utf-8')
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
            return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
        except Exception as e2:
            print(f"[AUTH] Error with bcrypt fallback: {e2}")
            return False

def get_password_hash(password: str) -> str:
    """Generar hash de contraseña"""
    try:
        # bcrypt tiene un límite de 72 bytes, no caracteres
        # Truncar la contraseña si excede este límite
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            # Truncar byte por byte hasta que esté bajo el límite
            while len(password.encode('utf-8')) > 72 and len(password) > 0:
                password = password[:-1]
        
        return pwd_context.hash(password)
    except Exception as e:
        print(f"[AUTH] Error hashing password: {e}")
        # Fallback usando bcrypt directamente
        import bcrypt
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crear token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    """Autenticar usuario"""
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def get_current_user(
    token: Optional[str] = Cookie(None, alias="access_token"),
    db: Session = Depends(get_db)
) -> models.User:
    """Obtener usuario actual desde token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user

def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Obtener usuario activo actual"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_admin_user(current_user: models.User = Depends(get_current_active_user)) -> models.User:
    """Obtener usuario administrador actual"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

# Función opcional para obtener usuario sin requerir autenticación
def get_current_user_optional(
    token: Optional[str] = Cookie(None, alias="access_token"),
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    """Obtener usuario actual (opcional, no lanza error si no está autenticado)"""
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        
        user = db.query(models.User).filter(models.User.email == email).first()
        return user
    except JWTError:
        return None