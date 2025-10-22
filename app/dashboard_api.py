# app/dashboard_api.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, desc
from decimal import Decimal
from typing import Optional, List
from datetime import datetime, date
import json

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
        func.extract("year", models.Reservation.check_in) == year
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

    # RESERVATIONS (contadores totales por mes de check-in)
    res_q = (
        db.query(
            func.extract("month", models.Reservation.check_in).label("m"),
            func.coalesce(func.count(models.Reservation.id), 0).label("total"),
        )
        .filter(and_(*res_filter))
        .group_by("m")
        .all()
    )
    res_total_map = {int(row.m): _i(row.total) for row in res_q}
    res_acc_map = res_total_map  # Por ahora, todas las reservas se consideran confirmadas
    res_pen_map = {m: 0 for m in range(1, 13)}  # Sin reservas pendientes por ahora

    # INCOMES (suma por status por mes)
    inc_q = (
        db.query(
            func.extract("month", models.Income.date).label("m"),
            func.coalesce(func.sum(case((models.Income.status == "CONFIRMED", models.Income.amount), else_=0)), 0).label("inc_acc"),
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

@router.get("/", response_class=HTMLResponse)
def dashboard_page():
    """Serve the dashboard HTML page"""
    import os
    try:
        # Get the path relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, "templates", "dashboard.html")
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard template not found")

@router.get("/content", response_class=HTMLResponse)
def dashboard_content(
    year: int = Query(default=datetime.now().year, description="Ej: 2025"),
    apartment_code: Optional[str] = Query(None, description="Opcional: SES01 para filtrar"),
    db: Session = Depends(get_db),
):
    """Serve dashboard content for HTMX updates"""
    import os
    try:
        # Get the path relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, "templates", "dashboard_content.html")
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Get basic dashboard data (without the problematic expenses_by_category)
        data = dashboard_monthly(year, apartment_code, db)
        
        # Inject data as JavaScript
        data_script = f"""
        <script>
        const dashboardData = {json.dumps(data, default=str)};
        if (typeof initializeDashboard === 'function') {{
            initializeDashboard(dashboardData);
        }}
        </script>
        """
        
        return HTMLResponse(content=content + data_script)
    except Exception as e:
        # Better error handling
        print(f"Error in dashboard_content: {e}")
        return HTMLResponse(content=f'<div class="error">Error loading dashboard: {str(e)}</div>')
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard content template not found")

@router.get("/data", response_model=DashboardMonthlyResponse)
def dashboard_data(
    year: int = Query(default=datetime.now().year, description="Ej: 2025"),
    apartment_code: Optional[str] = Query(None, description="Opcional: SES01 para filtrar"),
    db: Session = Depends(get_db),
):
    """Enhanced dashboard data with additional metrics"""
    # Get the base monthly data
    monthly_data = dashboard_monthly(year, apartment_code, db)
    
    # Skip expenses by category for now to avoid errors
    # TODO: Implement expenses by category breakdown later
    
    return monthly_data

@router.get("/apartments")
def get_apartments(db: Session = Depends(get_db)):
    """Get list of apartments for filter dropdown"""
    apartments = db.query(models.Apartment).filter(models.Apartment.is_active == True).all()
    return [{"code": apt.code, "name": apt.name or apt.code} for apt in apartments]

@router.get("/recent-expenses")
def get_recent_expenses(
    limit: int = Query(default=10, le=50),
    apartment_code: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get recent expenses for the activity feed"""
    q = db.query(models.Expense).join(models.Apartment)
    
    if apartment_code:
        q = q.filter(models.Apartment.code == apartment_code)
    
    expenses = q.order_by(desc(models.Expense.created_at)).limit(limit).all()
    
    return [
        {
            "id": exp.id,
            "date": exp.date.isoformat(),
            "amount": float(exp.amount_gross),
            "currency": exp.currency,
            "category": exp.category,
            "description": exp.description,
            "vendor": exp.vendor,
            "apartment_code": exp.apartment.code,
            "created_at": exp.created_at.isoformat() if exp.created_at else None
        }
        for exp in expenses
    ]

@router.get("/summary-stats")
def get_summary_stats(
    year: int = Query(default=datetime.now().year),
    apartment_code: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get summary statistics for the dashboard"""
    
    # Base filters
    apartment_id = None
    if apartment_code:
        apt = db.query(models.Apartment).filter(models.Apartment.code == apartment_code).first()
        if apt:
            apartment_id = apt.id
    
    # Current year filters
    current_filters = [func.extract("year", models.Expense.date) == year]
    if apartment_id:
        current_filters.append(models.Expense.apartment_id == apartment_id)
    
    # Previous year filters for comparison
    prev_filters = [func.extract("year", models.Expense.date) == year - 1]
    if apartment_id:
        prev_filters.append(models.Expense.apartment_id == apartment_id)
    
    # Current year totals
    current_expenses = db.query(
        func.coalesce(func.sum(models.Expense.amount_gross), 0)
    ).filter(and_(*current_filters)).scalar() or 0
    
    # Previous year totals for comparison
    prev_expenses = db.query(
        func.coalesce(func.sum(models.Expense.amount_gross), 0)
    ).filter(and_(*prev_filters)).scalar() or 0
    
    # Calculate change percentage
    expense_change = 0
    if prev_expenses > 0:
        expense_change = ((current_expenses - prev_expenses) / prev_expenses) * 100
    
    # Get income data (similar logic)
    inc_current_filters = [func.extract("year", models.Income.date) == year]
    inc_prev_filters = [func.extract("year", models.Income.date) == year - 1]
    if apartment_id:
        inc_current_filters.append(models.Income.apartment_id == apartment_id)
        inc_prev_filters.append(models.Income.apartment_id == apartment_id)
    
    current_income = db.query(
        func.coalesce(func.sum(models.Income.amount_gross), 0)
    ).filter(and_(*inc_current_filters)).scalar() or 0
    
    prev_income = db.query(
        func.coalesce(func.sum(models.Income.amount_gross), 0)
    ).filter(and_(*inc_prev_filters)).scalar() or 0
    
    income_change = 0
    if prev_income > 0:
        income_change = ((current_income - prev_income) / prev_income) * 100
    
    # Net profit
    net_profit = current_income - current_expenses
    prev_net = prev_income - prev_expenses
    net_change = 0
    if prev_net != 0:
        net_change = ((net_profit - prev_net) / abs(prev_net)) * 100
    
    # Profit margin
    profit_margin = (net_profit / current_income * 100) if current_income > 0 else 0
    
    # Average monthly values
    avg_monthly_income = current_income / 12
    avg_monthly_expenses = current_expenses / 12
    avg_monthly_net = net_profit / 12
    
    return {
        "total_income": float(current_income),
        "total_expenses": float(current_expenses),
        "net_profit": float(net_profit),
        "profit_margin": float(profit_margin),
        "avg_monthly_income": float(avg_monthly_income),
        "avg_monthly_expenses": float(avg_monthly_expenses),
        "avg_monthly_net": float(avg_monthly_net),
        "income_change": float(income_change),
        "expense_change": float(expense_change),
        "net_change": float(net_change),
        "year": year,
        "apartment_code": apartment_code
    }
