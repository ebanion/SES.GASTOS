# app/routers/incomes.py
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models, schemas
from ..auth import get_current_user_optional

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

def _to_detailed_out(row: models.Income) -> dict:
    """Convierte Income a dict con información detallada de reserva"""
    return {
        "id": str(row.id),
        "reservation_id": str(row.reservation_id) if row.reservation_id else None,
        "apartment_id": row.apartment_id,
        "apartment_code": row.apartment.code if row.apartment else None,
        "apartment_name": row.apartment.name if row.apartment else None,
        "date": row.date.isoformat(),
        "amount_gross": str(row.amount_gross),
        "currency": row.currency,
        "status": row.status,
        "non_refundable_at": row.non_refundable_at.isoformat() if row.non_refundable_at else None,
        "source": row.source,
        "guest_name": row.guest_name,
        "guest_email": row.guest_email,
        "booking_reference": row.booking_reference,
        "check_in_date": row.check_in_date.isoformat() if row.check_in_date else None,
        "check_out_date": row.check_out_date.isoformat() if row.check_out_date else None,
        "guests_count": row.guests_count,
        "processed_from_email": row.processed_from_email,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat() if row.updated_at else None
    }


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


@router.get("/reservations")
def list_reservation_incomes(
    apartment_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_optional)
):
    """
    Lista ingresos de reservas con información detallada
    Filtrado por usuario si no es admin
    """
    q = db.query(models.Income).filter(
        models.Income.processed_from_email == True
    )

    # Filtrar por apartamentos del usuario si no es admin
    if current_user and not current_user.is_admin:
        user_apartment_ids = [apt.id for apt in current_user.apartments]
        if not user_apartment_ids:
            return {"reservations": [], "total": 0}
        q = q.filter(models.Income.apartment_id.in_(user_apartment_ids))

    if apartment_id:
        q = q.filter(models.Income.apartment_id == apartment_id)

    if status:
        q = q.filter(models.Income.status == status)

    if source:
        q = q.filter(models.Income.source == source)

    total = q.count()
    rows = q.order_by(models.Income.created_at.desc()).limit(limit).all()
    
    return {
        "reservations": [_to_detailed_out(r) for r in rows],
        "total": total,
        "showing": len(rows)
    }


@router.get("/stats")
def get_income_stats(
    apartment_id: Optional[str] = Query(default=None),
    days: int = Query(default=30, le=365),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_optional)
):
    """
    Estadísticas de ingresos por reservas
    """
    from_date = datetime.now() - timedelta(days=days)
    
    q = db.query(models.Income).filter(
        models.Income.created_at >= from_date
    )

    # Filtrar por apartamentos del usuario si no es admin
    if current_user and not current_user.is_admin:
        user_apartment_ids = [apt.id for apt in current_user.apartments]
        if not user_apartment_ids:
            return {"error": "No apartments found for user"}
        q = q.filter(models.Income.apartment_id.in_(user_apartment_ids))

    if apartment_id:
        q = q.filter(models.Income.apartment_id == apartment_id)

    all_incomes = q.all()
    
    # Estadísticas generales
    total_reservations = len(all_incomes)
    confirmed_reservations = len([i for i in all_incomes if i.status == "CONFIRMED"])
    pending_reservations = len([i for i in all_incomes if i.status == "PENDING"])
    cancelled_reservations = len([i for i in all_incomes if i.status == "CANCELLED"])
    
    total_amount = sum(float(i.amount_gross) for i in all_incomes if i.status != "CANCELLED")
    confirmed_amount = sum(float(i.amount_gross) for i in all_incomes if i.status == "CONFIRMED")
    pending_amount = sum(float(i.amount_gross) for i in all_incomes if i.status == "PENDING")
    
    # Por fuente
    by_source = {}
    for source in ["BOOKING", "AIRBNB", "WEB", "MANUAL"]:
        source_incomes = [i for i in all_incomes if i.source == source]
        by_source[source] = {
            "count": len(source_incomes),
            "amount": sum(float(i.amount_gross) for i in source_incomes if i.status != "CANCELLED"),
            "confirmed": len([i for i in source_incomes if i.status == "CONFIRMED"]),
            "pending": len([i for i in source_incomes if i.status == "PENDING"]),
            "cancelled": len([i for i in source_incomes if i.status == "CANCELLED"])
        }
    
    # Próximos check-ins
    upcoming_checkins = [
        i for i in all_incomes 
        if i.check_in_date and i.check_in_date >= datetime.now().date() and i.status == "CONFIRMED"
    ]
    
    return {
        "period_days": days,
        "from_date": from_date.date().isoformat(),
        "summary": {
            "total_reservations": total_reservations,
            "confirmed_reservations": confirmed_reservations,
            "pending_reservations": pending_reservations,
            "cancelled_reservations": cancelled_reservations,
            "total_amount": total_amount,
            "confirmed_amount": confirmed_amount,
            "pending_amount": pending_amount
        },
        "by_source": by_source,
        "upcoming_checkins": len(upcoming_checkins)
    }


@router.get("/upcoming-checkins")
def get_upcoming_checkins(
    days: int = Query(default=7, le=30),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_optional)
):
    """
    Obtiene check-ins próximos
    """
    today = datetime.now().date()
    end_date = today + timedelta(days=days)
    
    q = db.query(models.Income).filter(
        models.Income.check_in_date >= today,
        models.Income.check_in_date <= end_date,
        models.Income.status == "CONFIRMED"
    )

    # Filtrar por apartamentos del usuario si no es admin
    if current_user and not current_user.is_admin:
        user_apartment_ids = [apt.id for apt in current_user.apartments]
        if not user_apartment_ids:
            return {"checkins": []}
        q = q.filter(models.Income.apartment_id.in_(user_apartment_ids))

    checkins = q.order_by(models.Income.check_in_date).all()
    
    # Agrupar por fecha
    by_date = {}
    for checkin in checkins:
        date_key = checkin.check_in_date.isoformat()
        if date_key not in by_date:
            by_date[date_key] = []
        
        by_date[date_key].append({
            "apartment_code": checkin.apartment.code if checkin.apartment else "N/A",
            "apartment_name": checkin.apartment.name if checkin.apartment else "N/A",
            "guest_name": checkin.guest_name,
            "booking_reference": checkin.booking_reference,
            "guests_count": checkin.guests_count,
            "source": checkin.source,
            "check_out_date": checkin.check_out_date.isoformat() if checkin.check_out_date else None,
            "amount": str(checkin.amount_gross)
        })
    
    return {
        "period_days": days,
        "checkins_by_date": by_date,
        "total_checkins": len(checkins)
    }

