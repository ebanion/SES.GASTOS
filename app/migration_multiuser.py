# app/migration_multiuser.py
"""
Migración de datos existentes al sistema multiusuario
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from .db import get_db, SessionLocal
from .models import User, Account, AccountUser, Apartment
from .auth_multiuser import get_password_hash, create_account_slug, ensure_unique_slug

def migrate_to_multiuser_system(db: Session) -> Dict[str, Any]:
    """
    Migrar apartamentos existentes al sistema multiusuario
    """
    results = {
        "apartments_migrated": 0,
        "accounts_created": 0,
        "users_created": 0,
        "errors": [],
        "details": []
    }
    
    try:
        # 1. Buscar apartamentos sin account_id
        orphan_apartments = db.query(Apartment).filter(
            Apartment.account_id.is_(None)
        ).all()
        
        if not orphan_apartments:
            results["message"] = "No hay apartamentos que migrar"
            return results
        
        # 2. Agrupar apartamentos por owner_email
        apartments_by_owner = {}
        for apt in orphan_apartments:
            owner_email = apt.owner_email or "sistema@sesgas.com"
            if owner_email not in apartments_by_owner:
                apartments_by_owner[owner_email] = []
            apartments_by_owner[owner_email].append(apt)
        
        # 3. Para cada owner_email, crear usuario y cuenta
        for owner_email, apartments in apartments_by_owner.items():
            try:
                # Verificar si ya existe usuario con este email
                user = db.query(User).filter(User.email == owner_email).first()
                
                if not user:
                    # Crear usuario
                    user = User(
                        email=owner_email,
                        full_name=f"Usuario {owner_email.split('@')[0]}",
                        password_hash=get_password_hash("123456"),  # Contraseña temporal
                        is_active=True
                    )
                    db.add(user)
                    db.flush()
                    results["users_created"] += 1
                    results["details"].append(f"Usuario creado: {owner_email}")
                
                # Crear cuenta para este usuario
                account_name = f"Cuenta {owner_email.split('@')[0]}"
                base_slug = create_account_slug(account_name)
                unique_slug = ensure_unique_slug(db, base_slug)
                
                account = Account(
                    name=account_name,
                    slug=unique_slug,
                    contact_email=owner_email,
                    description=f"Cuenta migrada automáticamente para {owner_email}",
                    max_apartments=len(apartments) + 10,  # Margen extra
                    trial_ends_at=datetime.now(timezone.utc) + timedelta(days=90)  # 90 días de trial
                )
                
                db.add(account)
                db.flush()
                results["accounts_created"] += 1
                results["details"].append(f"Cuenta creada: {account_name} ({unique_slug})")
                
                # Crear membresía como owner
                membership = AccountUser(
                    account_id=account.id,
                    user_id=user.id,
                    role="owner",
                    invitation_accepted_at=datetime.now(timezone.utc)
                )
                db.add(membership)
                
                # Asignar apartamentos a la cuenta
                for apt in apartments:
                    apt.account_id = account.id
                    results["apartments_migrated"] += 1
                    results["details"].append(f"Apartamento {apt.code} asignado a cuenta {account_name}")
                
            except Exception as e:
                error_msg = f"Error migrando apartamentos de {owner_email}: {str(e)}"
                results["errors"].append(error_msg)
                results["details"].append(error_msg)
        
        # 4. Crear cuenta "Sistema" para apartamentos sin owner_email
        system_apartments = [apt for apt in orphan_apartments if not apt.owner_email]
        if system_apartments:
            # Crear usuario sistema si no existe
            system_user = db.query(User).filter(User.email == "sistema@sesgas.com").first()
            if not system_user:
                system_user = User(
                    email="sistema@sesgas.com",
                    full_name="Sistema SES.GASTOS",
                    password_hash=get_password_hash("sistema123"),
                    is_active=True,
                    is_superadmin=True
                )
                db.add(system_user)
                db.flush()
                results["users_created"] += 1
            
            # Crear cuenta sistema
            system_account = Account(
                name="Sistema",
                slug="sistema",
                contact_email="sistema@sesgas.com",
                description="Cuenta del sistema para apartamentos sin propietario",
                max_apartments=1000
            )
            db.add(system_account)
            db.flush()
            results["accounts_created"] += 1
            
            # Crear membresía
            system_membership = AccountUser(
                account_id=system_account.id,
                user_id=system_user.id,
                role="owner",
                invitation_accepted_at=datetime.now(timezone.utc)
            )
            db.add(system_membership)
            
            # Asignar apartamentos sistema
            for apt in system_apartments:
                apt.account_id = system_account.id
                results["apartments_migrated"] += 1
        
        db.commit()
        results["success"] = True
        results["message"] = f"Migración completada: {results['apartments_migrated']} apartamentos, {results['accounts_created']} cuentas, {results['users_created']} usuarios"
        
    except Exception as e:
        db.rollback()
        results["success"] = False
        results["error"] = str(e)
        results["message"] = f"Error en migración: {str(e)}"
    
    return results

def create_superadmin_user(db: Session, email: str, password: str, full_name: str) -> Dict[str, Any]:
    """
    Crear usuario superadministrador
    """
    try:
        # Verificar que no exista
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return {
                "success": False,
                "error": "Ya existe un usuario con este email"
            }
        
        # Crear superadmin
        superadmin = User(
            email=email,
            full_name=full_name,
            password_hash=get_password_hash(password),
            is_active=True,
            is_superadmin=True
        )
        
        db.add(superadmin)
        db.commit()
        
        return {
            "success": True,
            "message": f"Superadministrador {email} creado exitosamente",
            "user_id": superadmin.id,
            "credentials": {
                "email": email,
                "password": password
            }
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }

def get_migration_status(db: Session) -> Dict[str, Any]:
    """
    Obtener estado de la migración
    """
    # Contar apartamentos sin cuenta
    orphan_apartments = db.query(func.count(Apartment.id)).filter(
        Apartment.account_id.is_(None)
    ).scalar()
    
    # Contar apartamentos con cuenta
    assigned_apartments = db.query(func.count(Apartment.id)).filter(
        Apartment.account_id.isnot(None)
    ).scalar()
    
    # Contar cuentas
    accounts_count = db.query(func.count(Account.id)).scalar()
    
    # Contar usuarios
    users_count = db.query(func.count(User.id)).scalar()
    superadmins_count = db.query(func.count(User.id)).filter(User.is_superadmin == True).scalar()
    
    return {
        "apartments": {
            "total": orphan_apartments + assigned_apartments,
            "orphan": orphan_apartments,
            "assigned": assigned_apartments,
            "migration_needed": orphan_apartments > 0
        },
        "accounts": {
            "total": accounts_count
        },
        "users": {
            "total": users_count,
            "superadmins": superadmins_count
        },
        "system_ready": orphan_apartments == 0 and accounts_count > 0 and superadmins_count > 0
    }