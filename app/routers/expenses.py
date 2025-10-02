# app/routers/expenses.py
from __future__ import annotations

import os
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/v1", tags=["expenses"])


# --- Guardia ADMIN_KEY (cabecera o query) ---
def _require_internal(
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
    key: str | None = Query(default=None),
):
    admin = os.getenv("ADMIN_KEY", "")
    provided = x_internal_key or key
    if not admin or provided != admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


# -------- GASTOS --------

@router.post(
    "/expenses",
    response_model=schemas.ExpenseOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_require_internal)],
)
def create_expense(payload: schemas.ExpenseIn, db: Session = Depends(get_db)):
    # Validar que exista el apartamento
    apt = db.query(models.Apartment).filter(models.Apartment.id == payload.apartment_id).first()
    if not apt:
        raise HTTPException(status_code=404, detail="apartment_not_found")

    e = models.Expense(
        apartment_id=payload.apartment_id,
        date=payload.date,
        category=payload.category,
        vendor=payload.vendor,
        description=payload.description,
        currency=payload.currency or "EUR",
        amount_gross=payload.amount_gross,
        vat_rate=payload.vat_rate,
        status=payload.status or "PENDING",
    )
    # Campo opcional: solo si el modelo tiene file_url y el payload lo trae
    if hasattr(models.Expense, "file_url") and getattr(payload, "file_url", None):
        setattr(e, "file_url", payload.file_url)

    db.add(e)
    db.commit()
    db.refresh(e)

    resp = {
        "id": e.id,
        "apartment_id": e.apartment_id,
        "date": e.date,
        "category": e.category,
        "vendor": e.vendor,
        "description": e.description,
        "currency": e.currency,
        "amount_gross": e.amount_gross,
        "vat_rate": e.vat_rate,
        "status": e.status,
    }
    if hasattr(e, "file_url"):
        resp["file_url"] = getattr(e, "file_url")

    return schemas.ExpenseOut(**resp)


@router.get("/expenses", response_model=list[schemas.ExpenseOut])
def list_expenses(apartment_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Expense)
    if apartment_id:
        q = q.filter(models.Expense.apartment_id == apartment_id)
    rows = q.order_by(models.Expense.date.desc()).limit(200).all()

    out = []
    for r in rows:
        item = {
            "id": r.id,
            "apartment_id": r.apartment_id,
            "date": r.date,
            "category": r.category,
            "vendor": r.vendor,
            "description": r.description,
            "currency": r.currency,
            "amount_gross": r.amount_gross,
            "vat_rate": r.vat_rate,
            "status": r.status,
        }
        if hasattr(r, "file_url"):
            item["file_url"] = getattr(r, "file_url")
        out.append(schemas.ExpenseOut(**item))
    return out
