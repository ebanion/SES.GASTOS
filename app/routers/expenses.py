from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
import os

router = APIRouter(prefix="/api/v1", tags=["expenses"])

def _require_internal(
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
    key: str | None = Query(default=None),
):
    admin = os.getenv("ADMIN_KEY", "")
    provided = x_internal_key or key
    if not admin or provided != admin:
        raise HTTPException(status_code=403, detail="Forbidden")

# -------- Apartamentos --------

@router.post("/apartments", response_model=schemas.ApartmentOut)
def create_apartment(
    payload: schemas.ApartmentIn,
    db: Session = Depends(get_db),
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
):
    _require_internal(x_internal_key)

    exists = db.query(models.Apartment).filter(models.Apartment.code == payload.code).first()
    if exists:
        raise HTTPException(409, "code already exists")

    apt = models.Apartment(
        code=payload.code,
        name=payload.name,
        owner_email=payload.owner_email,
        telegram_chat_id=payload.telegram_chat_id,
    )
    db.add(apt); db.commit(); db.refresh(apt)
    return schemas.ApartmentOut(id=apt.id, **payload.model_dump())

@router.get("/apartments", response_model=list[schemas.ApartmentOut])
def list_apartments(db: Session = Depends(get_db)):
    rows = db.query(models.Apartment).order_by(models.Apartment.created_at.desc()).all()
    return [schemas.ApartmentOut(id=r.id, code=r.code, name=r.name,
                                 owner_email=r.owner_email, telegram_chat_id=r.telegram_chat_id) for r in rows]

# -------- Gastos --------

@router.post("/expenses", response_model=schemas.ExpenseOut)
def create_expense(
    payload: schemas.ExpenseIn,
    db: Session = Depends(get_db),
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
):
    _require_internal(x_internal_key)

    apt = db.query(models.Apartment).filter(models.Apartment.id == payload.apartment_id).first()
    if not apt:
        raise HTTPException(404, "apartment_not_found")

    e = models.Expense(
        apartment_id=payload.apartment_id,
        date=payload.date,
        category=payload.category,
        vendor=payload.vendor,
        description=payload.description,
        currency=payload.currency,
        amount_gross=payload.amount_gross,
        vat_rate=payload.vat_rate,
        file_url=payload.file_url,
        status=payload.status or "PENDING",
    )
    db.add(e); db.commit(); db.refresh(e)
    return schemas.ExpenseOut(id=e.id, **payload.model_dump())

@router.get("/expenses", response_model=list[schemas.ExpenseOut])
def list_expenses(
    apartment_id: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Expense)
    if apartment_id:
        q = q.filter(models.Expense.apartment_id == apartment_id)
    rows = q.order_by(models.Expense.date.desc()).limit(200).all()
    out = []
    for r in rows:
        out.append(schemas.ExpenseOut(
            id=r.id, apartment_id=r.apartment_id, date=r.date, category=r.category,
            vendor=r.vendor, description=r.description, currency=r.currency,
            amount_gross=r.amount_gross, vat_rate=r.vat_rate, file_url=r.file_url,
            status=r.status
        ))
    return out
