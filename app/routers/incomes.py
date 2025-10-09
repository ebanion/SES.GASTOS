# app/routers/incomes.py
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/v1/incomes", tags=["incomes"])


def require_internal_key(
    x_internal_key: Optional[str] = Header(default=None, alias="X-Internal-Key"),
    key: Optional[str] = Query(default=None),
):
    import os
    admin = os.getenv("ADMIN_KEY", "")
    provided = x_internal_key or key
    if not admin or provided != admin:
        raise HTTPException(status_code=403, detail="Forbidden")


def _to_out(row: models.Income) -> schemas.IncomeOut:
    return schemas.IncomeOut(
        id=str(row.id),
        reservation_id=str(row.reservation_id) if row.reservation_id else None,
        apartment_id=row.apartment_id,
        date=row.date,
        amount_gross=row.amount_gross,
        currency=row.currency,
        status=row.status,
        non_refundable_at=row.non_refundable_at,
        source=row.source,
        created_at=row.created_at,
    )


@router.get("", response_model=list[schemas.IncomeOut])
def list_incomes(
    reservation_id: Optional[str] = Query(default=None),
    apartment_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),  # PENDING | CONFIRMED | CANCELLED
    db: Session = Depends(get_db),
):
    q = db.query(models.Income)

    if reservation_id:
        q = q.filter(models.Income.reservation_id == reservation_id)

    if apartment_id:
        q = q.filter(models.Income.apartment_id == apartment_id)

    if status:
        q = q.filter(models.Income.status == status)

    rows = q.order_by(models.Income.created_at.desc()).limit(200).all()
    return [_to_out(r) for r in rows]


@router.post("/from_reservation", response_model=schemas.IncomeOut,
             dependencies=[Depends(require_internal_key)])
def create_income_from_reservation(
    payload: schemas.IncomeFromReservationIn,
    db: Session = Depends(get_db),
):
    # 1) Buscar la reserva
    r = db.query(models.Reservation).filter(
        models.Reservation.id == payload.reservation_id
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="reservation_not_found")

    # Fecha base del ingreso = check_in
    income_date = r.check_in

    # no reembolsable en check_in - policy_days
    non_refundable_at = r.check_in - timedelta(days=payload.policy_days or 0)

    # Confirmado si ya pasamos la fecha de no reembolso
    today = datetime.now(timezone.utc).date()
    status = "CONFIRMED" if today >= non_refundable_at else "PENDING"

    inc = models.Income(
        reservation_id=str(r.id),
        apartment_id=payload.apartment_id or getattr(r, "apartment_id", None),
        date=income_date,
        amount_gross=payload.amount_gross,
        currency=payload.currency,
        status=status,
        non_refundable_at=non_refundable_at,
        source=payload.source or "reservation",
    )
    db.add(inc)
    db.commit()
    db.refresh(inc)

    return _to_out(inc)


@router.post("/{income_id}/cancel", response_model=schemas.IncomeOut,
             dependencies=[Depends(require_internal_key)])
def cancel_income(
    income_id: str,
    db: Session = Depends(get_db),
):
    inc = db.query(models.Income).filter(models.Income.id == income_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="income_not_found")

    if inc.status == "CONFIRMED":
        # política: no permitir cancelar ingresos ya confirmados
        raise HTTPException(status_code=409, detail="income_already_confirmed")

    inc.status = "CANCELLED"
    db.commit()
    db.refresh(inc)
    return _to_out(inc)


@router.post("/roll", dependencies=[Depends(require_internal_key)])
def roll_confirm_incomes(db: Session = Depends(get_db)):
    """
    Confirma (status = CONFIRMED) todos los ingresos PENDING cuya
    fecha 'non_refundable_at' sea <= hoy.
    """
    today = datetime.now(timezone.utc).date()
    q = db.query(models.Income).filter(
        models.Income.status == "PENDING",
        models.Income.non_refundable_at <= today,
    )
    rows = q.all()
    for inc in rows:
        inc.status = "CONFIRMED"
    db.commit()

    return {"ok": True, "confirmed": len(rows)}

