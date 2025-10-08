# app/routers/incomes.py
from __future__ import annotations

import os
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/v1/incomes", tags=["incomes"])

def require_internal_key(
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
    key: str | None = Query(default=None),
):
    admin = os.getenv("ADMIN_KEY", "")
    provided = x_internal_key or key
    if not admin or provided != admin:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/from_reservation",
             response_model=schemas.IncomeOut,
             dependencies=[Depends(require_internal_key)])
def create_income_from_reservation(
    payload: schemas.IncomeFromReservationIn,
    db: Session = Depends(get_db),
):
    # 1) Localiza la reserva
    r = db.query(models.Reservation).filter(models.Reservation.id == payload.reservation_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="reservation_not_found")

    # 2) Calcula fecha no reembolsable y estado inicial
    non_ref_at = None
    status = "CONFIRMED"
    if payload.non_refundable_days and payload.non_refundable_days > 0:
        non_ref_at = r.check_in - timedelta(days=payload.non_refundable_days)
        status = "PENDING" if date.today() < non_ref_at else "CONFIRMED"

    inc = models.Income(
        reservation_id=r.id,
        apartment_id=payload.apartment_id,  # puede ir a None si aún no lo sabemos
        date=r.check_in,
        amount_gross=payload.amount_gross,
        currency=payload.currency,
        status=status,
        non_refundable_at=non_ref_at,
        source=payload.source or "reservation",
    )
    db.add(inc); db.commit(); db.refresh(inc)

    return schemas.IncomeOut(
        id=inc.id,
        reservation_id=inc.reservation_id,
        apartment_id=inc.apartment_id,
        date=inc.date,
        amount_gross=inc.amount_gross,
        currency=inc.currency,
        status=inc.status,
        non_refundable_at=inc.non_refundable_at,
        source=inc.source,
        created_at=inc.created_at,
    )


@router.post("/{income_id}/cancel",
             response_model=schemas.IncomeOut,
             dependencies=[Depends(require_internal_key)])
def cancel_income(income_id: str, db: Session = Depends(get_db)):
    inc = db.query(models.Income).filter(models.Income.id == income_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="income_not_found")

    inc.status = "CANCELLED"
    db.commit(); db.refresh(inc)

    return schemas.IncomeOut(
        id=inc.id,
        reservation_id=inc.reservation_id,
        apartment_id=inc.apartment_id,
        date=inc.date,
        amount_gross=inc.amount_gross,
        currency=inc.currency,
        status=inc.status,
        non_refundable_at=inc.non_refundable_at,
        source=inc.source,
        created_at=inc.created_at,
    )


@router.post("/roll",
             dependencies=[Depends(require_internal_key)])
def roll_pending_incomes(db: Session = Depends(get_db)):
    """Confirma todos los ingresos PENDING cuya fecha no reembolsable ya pasó."""
    today = date.today()
    q = db.query(models.Income).filter(
        models.Income.status == "PENDING",
        models.Income.non_refundable_at.isnot(None),
        models.Income.non_refundable_at <= today,
    )
    count = 0
    for inc in q.all():
        inc.status = "CONFIRMED"
        count += 1
    if count:
        db.commit()
    return {"ok": True, "confirmed": count}


@router.get("",
            response_model=list[schemas.IncomeOut])
def list_incomes(
    reservation_id: str | None = None,
    apartment_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Income)
    if reservation_id:
        q = q.filter(models.Income.reservation_id == reservation_id)
    if apartment_id:
        q = q.filter(models.Income.apartment_id == apartment_id)
    if status:
        q = q.filter(models.Income.status == status)

    rows = q.order_by(models.Income.date.desc()).limit(200).all()

    return [
        schemas.IncomeOut(
            id=r.id,
            reservation_id=r.reservation_id,
            apartment_id=r.apartment_id,
            date=r.date,
            amount_gross=r.amount_gross,
            currency=r.currency,
            status=r.status,
            non_refundable_at=r.non_refundable_at,
            source=r.source,
            created_at=r.created_at,
        )
        for r in rows
    ]
