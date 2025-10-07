# app/routers/expenses.py
from __future__ import annotations

import os
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

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
    apt = db.query(models.Apartment).filter(models.Apartment.id == payload.apartment_id).first()
    if not apt:
        raise HTTPException(status_code=404, detail="apartment_not_found")

    e = models.Expense(
        apartment_id=payload.apartment_id,
        date=payload.date,
        amount=payload.amount_gross,  # <-- mapea al campo 'amount' del modelo
        currency=payload.currency,
        category=payload.category,
        description=payload.description,
        vendor=payload.vendor,
        invoice_number=payload.invoice_number,
        source=payload.source,
    )
    # Campos opcionales si existen en el modelo/DB
    if hasattr(models.Expense, "vat_rate"):
        e.vat_rate = payload.vat_rate
    if hasattr(models.Expense, "file_url"):
        e.file_url = payload.file_url
    if hasattr(models.Expense, "status"):
        e.status = payload.status

    db.add(e)
    db.commit()
    db.refresh(e)

    return schemas.ExpenseOut(
        id=e.id,
        apartment_id=e.apartment_id,
        date=e.date,
        amount_gross=e.amount,  # devolvemos con el nombre del schema
        currency=e.currency,
        category=e.category,
        description=e.description,
        vendor=e.vendor,
        invoice_number=e.invoice_number,
        source=e.source,
        vat_rate=getattr(e, "vat_rate", None),
        file_url=getattr(e, "file_url", None),
        status=getattr(e, "status", None),
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
            amount_gross=r.amount,
            currency=r.currency,
            category=r.category,
            description=r.description,
            vendor=r.vendor,
            invoice_number=r.invoice_number,
            source=r.source,
            vat_rate=getattr(r, "vat_rate", None),
            file_url=getattr(r, "file_url", None),
            status=getattr(r, "status", None),
        )
        for r in rows
    ]

