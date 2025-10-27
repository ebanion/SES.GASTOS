# app/routers/accounts.py
"""
Router para gestión de cuentas de anfitrión (tenants)
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc

from ..db import get_db
from ..models import Account, User, AccountUser, Apartment, Expense, Income
from ..schemas import (
    AccountCreate, AccountUpdate, AccountOut, 
    AccountUserCreate, AccountUserUpdate, AccountUserOut,
    UserOut
)
from ..auth_multiuser import (
    get_current_user, get_current_account, require_superadmin,
    require_owner, require_admin_or_owner, require_member_or_above,
    create_account_slug, ensure_unique_slug, get_user_accounts,
    get_password_hash
)

router = APIRouter(prefix="/api/v1/accounts", tags=["Cuentas"])

# ---------- GESTIÓN DE CUENTAS ----------

@router.post("/", response_model=AccountOut)
async def create_account(
    account_data: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crear nueva cuenta de anfitrión
    Solo superadmins o usuarios pueden crear cuentas
    """
    # Crear slug único
    base_slug = create_account_slug(account_data.name)
    unique_slug = ensure_unique_slug(db, base_slug)
    
    # Crear la cuenta
    account = Account(
        name=account_data.name,
        slug=unique_slug,
        description=account_data.description,
        contact_email=account_data.contact_email,
        phone=account_data.phone,
        address=account_data.address,
        tax_id=account_data.tax_id,
        trial_ends_at=datetime.now(timezone.utc) + timedelta(days=30)  # 30 días de trial
    )
    
    db.add(account)
    db.flush()  # Para obtener el ID
    
    # Hacer al usuario creador el owner de la cuenta
    membership = AccountUser(
        account_id=account.id,
        user_id=current_user.id,
        role="owner",
        invitation_accepted_at=datetime.now(timezone.utc)
    )
    
    db.add(membership)
    db.commit()
    db.refresh(account)
    
    # Agregar estadísticas
    account_out = AccountOut.from_orm(account)
    account_out.apartments_count = 0
    account_out.users_count = 1
    
    return account_out

@router.get("/", response_model=List[AccountOut])
async def list_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_stats: bool = Query(False, description="Incluir estadísticas de apartamentos y usuarios")
):
    """
    Listar cuentas del usuario actual
    Superadmins ven todas las cuentas
    """
    if current_user.is_superadmin:
        # Superadmin ve todas las cuentas
        accounts = db.query(Account).order_by(desc(Account.created_at)).all()
    else:
        # Usuario normal ve solo sus cuentas
        accounts = get_user_accounts(db, current_user.id)
    
    # Agregar estadísticas si se solicita
    result = []
    for account in accounts:
        account_out = AccountOut.from_orm(account)
        
        if include_stats:
            # Contar apartamentos
            apartments_count = db.query(func.count(Apartment.id)).filter(
                Apartment.account_id == account.id
            ).scalar()
            
            # Contar usuarios
            users_count = db.query(func.count(AccountUser.id)).filter(
                and_(
                    AccountUser.account_id == account.id,
                    AccountUser.is_active == True
                )
            ).scalar()
            
            account_out.apartments_count = apartments_count
            account_out.users_count = users_count
        
        result.append(account_out)
    
    return result

@router.get("/{account_id}", response_model=AccountOut)
async def get_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener detalles de una cuenta específica"""
    # Verificar acceso
    if not current_user.is_superadmin:
        user_accounts = get_user_accounts(db, current_user.id)
        if not any(acc.id == account_id for acc in user_accounts):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes acceso a esta cuenta"
            )
    
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada"
        )
    
    # Agregar estadísticas
    account_out = AccountOut.from_orm(account)
    
    # Contar apartamentos
    apartments_count = db.query(func.count(Apartment.id)).filter(
        Apartment.account_id == account.id
    ).scalar()
    
    # Contar usuarios
    users_count = db.query(func.count(AccountUser.id)).filter(
        and_(
            AccountUser.account_id == account.id,
            AccountUser.is_active == True
        )
    ).scalar()
    
    account_out.apartments_count = apartments_count
    account_out.users_count = users_count
    
    return account_out

@router.patch("/{account_id}", response_model=AccountOut)
async def update_account(
    account_id: str,
    account_data: AccountUpdate,
    membership: AccountUser = Depends(require_admin_or_owner),
    db: Session = Depends(get_db)
):
    """Actualizar cuenta (solo admins y owners)"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada"
        )
    
    # Actualizar campos
    update_data = account_data.dict(exclude_unset=True)
    
    # Si se cambia el nombre, actualizar el slug
    if "name" in update_data:
        base_slug = create_account_slug(update_data["name"])
        if base_slug != account.slug:
            unique_slug = ensure_unique_slug(db, base_slug)
            update_data["slug"] = unique_slug
    
    for field, value in update_data.items():
        setattr(account, field, value)
    
    account.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(account)
    
    return AccountOut.from_orm(account)

@router.delete("/{account_id}")
async def delete_account(
    account_id: str,
    membership: AccountUser = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """Eliminar cuenta (solo owners)"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada"
        )
    
    # Verificar que no tenga apartamentos activos
    active_apartments = db.query(func.count(Apartment.id)).filter(
        and_(
            Apartment.account_id == account_id,
            Apartment.is_active == True
        )
    ).scalar()
    
    if active_apartments > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede eliminar la cuenta. Tiene {active_apartments} apartamentos activos."
        )
    
    # Eliminar cuenta (cascade eliminará membresías y apartamentos)
    db.delete(account)
    db.commit()
    
    return {"message": "Cuenta eliminada exitosamente"}

# ---------- GESTIÓN DE USUARIOS EN CUENTAS ----------

@router.get("/{account_id}/users", response_model=List[AccountUserOut])
async def list_account_users(
    account_id: str,
    membership: AccountUser = Depends(require_member_or_above),
    db: Session = Depends(get_db)
):
    """Listar usuarios de una cuenta"""
    memberships = db.query(AccountUser).options(
        joinedload(AccountUser.user)
    ).filter(
        and_(
            AccountUser.account_id == account_id,
            AccountUser.is_active == True
        )
    ).order_by(AccountUser.created_at).all()
    
    result = []
    for membership in memberships:
        membership_out = AccountUserOut.from_orm(membership)
        membership_out.user_email = membership.user.email
        membership_out.user_full_name = membership.user.full_name
        result.append(membership_out)
    
    return result

@router.post("/{account_id}/users", response_model=AccountUserOut)
async def invite_user_to_account(
    account_id: str,
    user_data: AccountUserCreate,
    membership: AccountUser = Depends(require_admin_or_owner),
    db: Session = Depends(get_db)
):
    """Invitar usuario a una cuenta"""
    # Buscar usuario por email
    user = db.query(User).filter(User.email == user_data.user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Verificar que no esté ya en la cuenta
    existing_membership = db.query(AccountUser).filter(
        and_(
            AccountUser.account_id == account_id,
            AccountUser.user_id == user.id
        )
    ).first()
    
    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya pertenece a esta cuenta"
        )
    
    # Crear membresía
    new_membership = AccountUser(
        account_id=account_id,
        user_id=user.id,
        role=user_data.role,
        permissions=user_data.permissions,
        invited_by=membership.user_id,
        invitation_accepted_at=datetime.now(timezone.utc)  # Auto-aceptar por ahora
    )
    
    db.add(new_membership)
    db.commit()
    db.refresh(new_membership)
    
    # Preparar respuesta
    membership_out = AccountUserOut.from_orm(new_membership)
    membership_out.user_email = user.email
    membership_out.user_full_name = user.full_name
    
    return membership_out

@router.patch("/{account_id}/users/{user_id}", response_model=AccountUserOut)
async def update_user_role(
    account_id: str,
    user_id: str,
    user_data: AccountUserUpdate,
    membership: AccountUser = Depends(require_admin_or_owner),
    db: Session = Depends(get_db)
):
    """Actualizar rol de usuario en la cuenta"""
    target_membership = db.query(AccountUser).filter(
        and_(
            AccountUser.account_id == account_id,
            AccountUser.user_id == user_id
        )
    ).first()
    
    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado en esta cuenta"
        )
    
    # No permitir que un admin cambie el rol de un owner
    if target_membership.role == "owner" and membership.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un owner puede modificar a otro owner"
        )
    
    # Actualizar campos
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(target_membership, field, value)
    
    target_membership.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(target_membership)
    
    return AccountUserOut.from_orm(target_membership)

@router.delete("/{account_id}/users/{user_id}")
async def remove_user_from_account(
    account_id: str,
    user_id: str,
    membership: AccountUser = Depends(require_admin_or_owner),
    db: Session = Depends(get_db)
):
    """Remover usuario de la cuenta"""
    target_membership = db.query(AccountUser).filter(
        and_(
            AccountUser.account_id == account_id,
            AccountUser.user_id == user_id
        )
    ).first()
    
    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado en esta cuenta"
        )
    
    # No permitir remover al último owner
    if target_membership.role == "owner":
        owners_count = db.query(func.count(AccountUser.id)).filter(
            and_(
                AccountUser.account_id == account_id,
                AccountUser.role == "owner",
                AccountUser.is_active == True
            )
        ).scalar()
        
        if owners_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede remover al último owner de la cuenta"
            )
    
    # Remover membresía
    db.delete(target_membership)
    db.commit()
    
    return {"message": "Usuario removido de la cuenta exitosamente"}

# ---------- ESTADÍSTICAS DE CUENTA ----------

@router.get("/{account_id}/stats")
async def get_account_stats(
    account_id: str,
    membership: AccountUser = Depends(require_member_or_above),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de la cuenta"""
    # Contar apartamentos
    apartments_count = db.query(func.count(Apartment.id)).filter(
        Apartment.account_id == account_id
    ).scalar()
    
    active_apartments = db.query(func.count(Apartment.id)).filter(
        and_(
            Apartment.account_id == account_id,
            Apartment.is_active == True
        )
    ).scalar()
    
    # Contar gastos del mes actual
    from datetime import date
    current_month_start = date.today().replace(day=1)
    
    monthly_expenses = db.query(func.sum(Expense.amount_gross)).join(Apartment).filter(
        and_(
            Apartment.account_id == account_id,
            Expense.date >= current_month_start
        )
    ).scalar() or 0
    
    # Contar ingresos del mes actual
    monthly_incomes = db.query(func.sum(Income.amount_gross)).join(Apartment).filter(
        and_(
            Apartment.account_id == account_id,
            Income.date >= current_month_start,
            Income.status == "CONFIRMED"
        )
    ).scalar() or 0
    
    # Contar usuarios
    users_count = db.query(func.count(AccountUser.id)).filter(
        and_(
            AccountUser.account_id == account_id,
            AccountUser.is_active == True
        )
    ).scalar()
    
    return {
        "account_id": account_id,
        "apartments": {
            "total": apartments_count,
            "active": active_apartments
        },
        "users_count": users_count,
        "current_month": {
            "expenses": float(monthly_expenses),
            "incomes": float(monthly_incomes),
            "net": float(monthly_incomes - monthly_expenses)
        }
    }