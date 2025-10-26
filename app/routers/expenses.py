# app/routers/expenses.py
from __future__ import annotations

import os
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/v1/expenses", tags=["expenses"])

def require_internal_key(
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
    key: str | None = Query(default=None),
):
    admin = os.getenv("ADMIN_KEY", "")
    provided = x_internal_key or key
    if not admin or provided != admin:
        raise HTTPException(status_code=403, detail="Forbidden")

@router.post("", response_model=schemas.ExpenseOut, dependencies=[Depends(require_internal_key)])
def create_expense(payload: schemas.ExpenseIn, db: Session = Depends(get_db)):
    # 1) existe apartment?
    apt = (
        db.query(models.Apartment)
        .filter(models.Apartment.id == str(payload.apartment_id))
        .first()
    )
    if not apt:
        raise HTTPException(status_code=404, detail="apartment_not_found")

    # 2) construir gasto alineado a modelo/DB
    e = models.Expense(
        apartment_id=str(payload.apartment_id),
        date=payload.date,
        amount_gross=payload.amount_gross,
        currency=payload.currency,
        category=payload.category,
        description=payload.description,
        vendor=payload.vendor,
        invoice_number=payload.invoice_number,
        source=payload.source,
        vat_rate=payload.vat_rate,
        file_url=payload.file_url,
        status=payload.status,
    )

    try:
        db.add(e)
        db.commit()
        db.refresh(e)
    except SQLAlchemyError as ex:
        db.rollback()
        # Devuelve el mensaje para ver exactamente qué columna/dato falla
        raise HTTPException(status_code=400, detail=f"db_error: {str(ex.orig) if hasattr(ex, 'orig') else str(ex)}")

    return schemas.ExpenseOut(
        id=e.id,
        apartment_id=e.apartment_id,
        date=e.date,
        amount_gross=e.amount_gross,  # <-- mismo nombre
        currency=e.currency,
        category=e.category,
        description=e.description,
        vendor=e.vendor,
        invoice_number=e.invoice_number,
        source=e.source,
        vat_rate=e.vat_rate,
        file_url=e.file_url,
        status=e.status,
    )

@router.get("", response_model=list[schemas.ExpenseOut])
def list_expenses(
    apartment_id: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Expense)
    if apartment_id:
        q = q.filter(models.Expense.apartment_id == apartment_id)

    rows = q.order_by(models.Expense.date.desc()).limit(200).all()

    return [
        schemas.ExpenseOut(
            id=r.id,
            apartment_id=r.apartment_id,
            date=r.date,
            amount_gross=r.amount_gross,
            currency=r.currency,
            category=r.category,
            description=r.description,
            vendor=r.vendor,
            invoice_number=r.invoice_number,
            source=r.source,
            vat_rate=r.vat_rate,
            file_url=r.file_url,
            status=r.status,
        )
        for r in rows
    ]

@router.get("/{expense_id}", response_model=schemas.ExpenseOut)
def get_expense(expense_id: str, db: Session = Depends(get_db)):
    """Obtener gasto por ID"""
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="expense_not_found")
    
    return schemas.ExpenseOut(
        id=expense.id,
        apartment_id=expense.apartment_id,
        date=expense.date,
        amount_gross=expense.amount_gross,
        currency=expense.currency,
        category=expense.category,
        description=expense.description,
        vendor=expense.vendor,
        invoice_number=expense.invoice_number,
        source=expense.source,
        vat_rate=expense.vat_rate,
        file_url=expense.file_url,
        status=expense.status,
    )

@router.put("/{expense_id}", response_model=schemas.ExpenseOut, dependencies=[Depends(require_internal_key)])
def update_expense(expense_id: str, payload: schemas.ExpenseIn, db: Session = Depends(get_db)):
    """Actualizar gasto completo"""
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="expense_not_found")
    
    # Verificar que el apartamento existe
    apt = db.query(models.Apartment).filter(models.Apartment.id == str(payload.apartment_id)).first()
    if not apt:
        raise HTTPException(status_code=404, detail="apartment_not_found")
    
    # Actualizar todos los campos
    expense.apartment_id = str(payload.apartment_id)
    expense.date = payload.date
    expense.amount_gross = payload.amount_gross
    expense.currency = payload.currency
    expense.category = payload.category
    expense.description = payload.description
    expense.vendor = payload.vendor
    expense.invoice_number = payload.invoice_number
    expense.source = payload.source
    expense.vat_rate = payload.vat_rate
    expense.file_url = payload.file_url
    expense.status = payload.status
    
    try:
        db.commit()
        db.refresh(expense)
    except SQLAlchemyError as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"update_error: {str(ex.orig) if hasattr(ex, 'orig') else str(ex)}")
    
    return schemas.ExpenseOut(
        id=expense.id,
        apartment_id=expense.apartment_id,
        date=expense.date,
        amount_gross=expense.amount_gross,
        currency=expense.currency,
        category=expense.category,
        description=expense.description,
        vendor=expense.vendor,
        invoice_number=expense.invoice_number,
        source=expense.source,
        vat_rate=expense.vat_rate,
        file_url=expense.file_url,
        status=expense.status,
    )

@router.patch("/{expense_id}", response_model=schemas.ExpenseOut, dependencies=[Depends(require_internal_key)])
def patch_expense(expense_id: str, updates: dict, db: Session = Depends(get_db)):
    """Actualizar gasto parcialmente"""
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="expense_not_found")
    
    # Campos permitidos para actualizar
    allowed_fields = {
        "apartment_id", "date", "amount_gross", "currency", "category", 
        "description", "vendor", "invoice_number", "source", "vat_rate", 
        "file_url", "status"
    }
    
    for field, value in updates.items():
        if field in allowed_fields and hasattr(expense, field):
            # Validar apartamento si se está cambiando
            if field == "apartment_id" and value:
                apt = db.query(models.Apartment).filter(models.Apartment.id == str(value)).first()
                if not apt:
                    raise HTTPException(status_code=404, detail="apartment_not_found")
                setattr(expense, field, str(value))
            else:
                setattr(expense, field, value)
    
    try:
        db.commit()
        db.refresh(expense)
    except SQLAlchemyError as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"patch_error: {str(ex.orig) if hasattr(ex, 'orig') else str(ex)}")
    
    return schemas.ExpenseOut(
        id=expense.id,
        apartment_id=expense.apartment_id,
        date=expense.date,
        amount_gross=expense.amount_gross,
        currency=expense.currency,
        category=expense.category,
        description=expense.description,
        vendor=expense.vendor,
        invoice_number=expense.invoice_number,
        source=expense.source,
        vat_rate=expense.vat_rate,
        file_url=expense.file_url,
        status=expense.status,
    )

@router.delete("/{expense_id}", dependencies=[Depends(require_internal_key)])
def delete_expense(expense_id: str, db: Session = Depends(get_db)):
    """Eliminar gasto"""
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="expense_not_found")
    
    # Guardar información para la respuesta
    expense_info = {
        "id": expense.id,
        "apartment_id": expense.apartment_id,
        "date": str(expense.date),
        "amount_gross": float(expense.amount_gross),
        "description": expense.description,
        "vendor": expense.vendor
    }
    
    try:
        db.delete(expense)
        db.commit()
        return {
            "success": True,
            "message": f"Gasto eliminado exitosamente",
            "deleted_expense": expense_info
        }
    except SQLAlchemyError as ex:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"delete_error: {str(ex.orig) if hasattr(ex, 'orig') else str(ex)}")

@router.get("/by-apartment/{apartment_id}", response_model=list[schemas.ExpenseOut])
def get_expenses_by_apartment(apartment_id: str, db: Session = Depends(get_db)):
    """Obtener todos los gastos de un apartamento específico"""
    # Verificar que el apartamento existe
    apt = db.query(models.Apartment).filter(models.Apartment.id == apartment_id).first()
    if not apt:
        raise HTTPException(status_code=404, detail="apartment_not_found")
    
    expenses = db.query(models.Expense).filter(
        models.Expense.apartment_id == apartment_id
    ).order_by(models.Expense.date.desc()).all()
    
    return [
        schemas.ExpenseOut(
            id=expense.id,
            apartment_id=expense.apartment_id,
            date=expense.date,
            amount_gross=expense.amount_gross,
            currency=expense.currency,
            category=expense.category,
            description=expense.description,
            vendor=expense.vendor,
            invoice_number=expense.invoice_number,
            source=expense.source,
            vat_rate=expense.vat_rate,
            file_url=expense.file_url,
            status=expense.status,
        )
        for expense in expenses
    ]



