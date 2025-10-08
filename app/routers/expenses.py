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



