# app/dashboard_api.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
from decimal import Decimal
from typing import Optional, List

from app.db import get_db
from app import models
from app.schemas import DashboardMonthSummary, DashboardMonthlyResponse

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

def _f(x) -> float:
    # Convierte Decimal/None en float seguro
    if x is None: 
        return 0.0
    if isinstance(x, Decimal):
        return float(x)
    return float(x)

def _i(x) -> int:
    return int(x or 0)

@router.get("/monthly", response_model=DashboardMonthlyResponse)
def dashboard_monthly(
    year: int = Query(..., description="Ej: 2025"),
    apartment_code: Optional[str] = Query(None, description="Opcional: SES01 para filtrar"),
    db: Session = Depends(get_db),
):
    # Resuelve apartment_id si llega apartment_code
    apartment_id = None
    if apartment_code:
        apt = db.query(models.Apartment).filter(models.Apartment.code == apartment_code).first()
        if not apt:
            # no existe ese código: devolvemos meses a cero
            return {
                "year": year,
                "items": [
                    DashboardMonthSummary(
                        month=m,
                        incomes_accepted=0.0,
                        incomes_pending=0.0,
                        reservations_accepted=0,
                        reservations_pending=0,
                        expenses=0.0,
                        net=0.0,
                    )
                    for m in range(1, 13)
                ],
            }
        apartment_id = apt.id

    # Filtros comunes
    exp_filter = [
        func.extract("year", models.Expense.date) == year
    ]
    res_filter = [
        func.extract("year", models.Reservation.checkin_date) == year
    ]
    inc_filter = [
        func.extract("year", models.Income.date) == year
    ]
    if apartment_id:
        exp_filter.append(models.Expense.apartment_id == apartment_id)
        res_filter.append(models.Reservation.apartment_id == apartment_id)
        inc_filter.append(models.Income.apartment_id == apartment_id)

    # --- Aggregates seguros con COALESCE ---
    # EXPENSES (suma por mes)
    expenses_q = (
        db.query(
            func.extract("month", models.Expense.date).label("m"),
            func.coalesce(func.sum(models.Expense.amount_gross), 0).label("total_exp"),
        )
        .filter(and_(*exp_filter))
        .group_by("m")
        .all()
    )
    expenses_map = {int(row.m): _f(row.total_exp) for row in expenses_q}

    # RESERVATIONS (contadores por status por mes de check-in)
    res_q = (
        db.query(
            func.extract("month", models.Reservation.checkin_date).label("m"),
            func.coalesce(func.sum(case((models.Reservation.status == "ACCEPTED", 1), else_=0)), 0).label("acc"),
            func.coalesce(func.sum(case((models.Reservation.status == "PENDING", 1), else_=0)), 0).label("pen"),
        )
        .filter(and_(*res_filter))
        .group_by("m")
        .all()
    )
    res_acc_map = {int(row.m): _i(row.acc) for row in res_q}
    res_pen_map = {int(row.m): _i(row.pen) for row in res_q}

    # INCOMES (suma por status por mes)
    inc_q = (
        db.query(
            func.extract("month", models.Income.date).label("m"),
            func.coalesce(func.sum(case((models.Income.status == "ACCEPTED", models.Income.amount), else_=0)), 0).label("inc_acc"),
            func.coalesce(func.sum(case((models.Income.status == "PENDING",  models.Income.amount), else_=0)), 0).label("inc_pen"),
        )
        .filter(and_(*inc_filter))
        .group_by("m")
        .all()
    )
    inc_acc_map = {int(row.m): _f(row.inc_acc) for row in inc_q}
    inc_pen_map = {int(row.m): _f(row.inc_pen) for row in inc_q}

    # Monta los 12 meses (1..12) con defaults a cero
    items: List[DashboardMonthSummary] = []
    for m in range(1, 13):
        incomes_accepted  = inc_acc_map.get(m, 0.0)
        incomes_pending   = inc_pen_map.get(m, 0.0)
        expenses          = expenses_map.get(m, 0.0)
        reservations_acc  = res_acc_map.get(m, 0)
        reservations_pen  = res_pen_map.get(m, 0)
        net               = (incomes_accepted + incomes_pending) - expenses

        items.append(
            DashboardMonthSummary(
                month=m,
                incomes_accepted=incomes_accepted,
                incomes_pending=incomes_pending,
                reservations_accepted=reservations_acc,
                reservations_pending=reservations_pen,
                expenses=expenses,
                net=net,
            )
        )

    return {"year": year, "items": items}
