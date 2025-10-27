# app/routers/real_time_api.py
"""
APIs optimizadas para actualizaciones en tiempo real
"""
from __future__ import annotations
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..db import get_db
from .. import models

router = APIRouter(prefix="/api/realtime", tags=["realtime"])

def require_admin_key(key: str = Query(..., description="Admin key")):
    """Verificar clave de administrador"""
    admin_key = os.getenv("ADMIN_KEY", "admin123")
    if key != admin_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return True

@router.get("/incomes")
def get_incomes_realtime(
    key: str = Query(...),
    apartment_id: str = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin_key)
):
    """Obtener ingresos con información completa para actualización en tiempo real"""
    
    try:
        query = db.query(models.Income).join(
            models.Apartment, 
            models.Income.apartment_id == models.Apartment.id,
            isouter=True
        )
        
        if apartment_id:
            query = query.filter(models.Income.apartment_id == apartment_id)
        
        incomes = query.order_by(models.Income.created_at.desc()).limit(limit).all()
        
        result = []
        for income in incomes:
            apartment = db.query(models.Apartment).filter(
                models.Apartment.id == income.apartment_id
            ).first() if income.apartment_id else None
            
            result.append({
                "id": str(income.id),
                "reservation_id": income.reservation_id,
                "apartment_id": income.apartment_id,
                "apartment_code": apartment.code if apartment else "N/A",
                "apartment_name": apartment.name if apartment else "Sin apartamento",
                "date": income.date.isoformat(),
                "amount_gross": str(income.amount_gross),
                "currency": income.currency,
                "status": income.status,
                "source": income.source,
                "guest_name": income.guest_name,
                "guest_email": income.guest_email,
                "booking_reference": income.booking_reference,
                "check_in_date": income.check_in_date.isoformat() if income.check_in_date else None,
                "check_out_date": income.check_out_date.isoformat() if income.check_out_date else None,
                "guests_count": income.guests_count,
                "created_at": income.created_at.isoformat(),
                "updated_at": income.updated_at.isoformat() if income.updated_at else None
            })
        
        return {
            "success": True,
            "incomes": result,
            "total": len(result),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching incomes: {str(e)}")

@router.get("/expenses")
def get_expenses_realtime(
    key: str = Query(...),
    apartment_id: str = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin_key)
):
    """Obtener gastos con información completa para actualización en tiempo real"""
    
    try:
        query = db.query(models.Expense).join(
            models.Apartment,
            models.Expense.apartment_id == models.Apartment.id,
            isouter=True
        )
        
        if apartment_id:
            query = query.filter(models.Expense.apartment_id == apartment_id)
        
        expenses = query.order_by(models.Expense.created_at.desc()).limit(limit).all()
        
        result = []
        for expense in expenses:
            apartment = db.query(models.Apartment).filter(
                models.Apartment.id == expense.apartment_id
            ).first()
            
            result.append({
                "id": expense.id,
                "apartment_id": expense.apartment_id,
                "apartment_code": apartment.code if apartment else "N/A",
                "apartment_name": apartment.name if apartment else "Sin apartamento",
                "date": expense.date.isoformat(),
                "amount_gross": str(expense.amount_gross),
                "currency": expense.currency,
                "category": expense.category,
                "description": expense.description,
                "vendor": expense.vendor,
                "invoice_number": expense.invoice_number,
                "source": expense.source,
                "vat_rate": expense.vat_rate,
                "status": expense.status,
                "created_at": expense.created_at.isoformat(),
                "updated_at": expense.updated_at.isoformat() if expense.updated_at else None
            })
        
        return {
            "success": True,
            "expenses": result,
            "total": len(result),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching expenses: {str(e)}")

@router.get("/apartments")
def get_apartments_realtime(
    key: str = Query(...),
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin_key)
):
    """Obtener apartamentos con estadísticas para actualización en tiempo real"""
    
    try:
        apartments = db.query(models.Apartment).order_by(models.Apartment.created_at.desc()).all()
        
        result = []
        for apartment in apartments:
            # Contar gastos e ingresos
            expenses_count = db.query(models.Expense).filter(
                models.Expense.apartment_id == apartment.id
            ).count()
            
            incomes_count = db.query(models.Income).filter(
                models.Income.apartment_id == apartment.id
            ).count()
            
            # Calcular totales del mes actual
            current_month = datetime.now().replace(day=1)
            
            monthly_expenses = db.query(func.sum(models.Expense.amount_gross)).filter(
                models.Expense.apartment_id == apartment.id,
                models.Expense.date >= current_month.date()
            ).scalar() or 0
            
            monthly_incomes = db.query(func.sum(models.Income.amount_gross)).filter(
                models.Income.apartment_id == apartment.id,
                models.Income.date >= current_month.date(),
                models.Income.status == "CONFIRMED"
            ).scalar() or 0
            
            result.append({
                "id": apartment.id,
                "code": apartment.code,
                "name": apartment.name,
                "owner_email": apartment.owner_email,
                "is_active": apartment.is_active,
                "created_at": apartment.created_at.isoformat(),
                "stats": {
                    "total_expenses": expenses_count,
                    "total_incomes": incomes_count,
                    "monthly_expenses": float(monthly_expenses),
                    "monthly_incomes": float(monthly_incomes),
                    "monthly_net": float(monthly_incomes - monthly_expenses)
                }
            })
        
        return {
            "success": True,
            "apartments": result,
            "total": len(result),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching apartments: {str(e)}")

@router.get("/dashboard-stats")
def get_dashboard_stats_realtime(
    key: str = Query(...),
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin_key)
):
    """Obtener estadísticas del dashboard optimizadas para tiempo real"""
    
    try:
        # Estadísticas generales
        total_apartments = db.query(models.Apartment).filter(models.Apartment.is_active == True).count()
        total_expenses = db.query(models.Expense).count()
        total_incomes = db.query(models.Income).count()
        
        # Estadísticas del mes actual
        current_month = datetime.now().replace(day=1)
        
        monthly_expenses = db.query(func.sum(models.Expense.amount_gross)).filter(
            models.Expense.date >= current_month.date()
        ).scalar() or 0
        
        monthly_incomes_confirmed = db.query(func.sum(models.Income.amount_gross)).filter(
            models.Income.date >= current_month.date(),
            models.Income.status == "CONFIRMED"
        ).scalar() or 0
        
        monthly_incomes_pending = db.query(func.sum(models.Income.amount_gross)).filter(
            models.Income.date >= current_month.date(),
            models.Income.status == "PENDING"
        ).scalar() or 0
        
        # Actividad reciente (últimos 7 días)
        week_ago = datetime.now() - timedelta(days=7)
        
        recent_expenses = db.query(models.Expense).filter(
            models.Expense.created_at >= week_ago
        ).count()
        
        recent_incomes = db.query(models.Income).filter(
            models.Income.created_at >= week_ago
        ).count()
        
        return {
            "success": True,
            "totals": {
                "active_apartments": total_apartments,
                "total_expenses": total_expenses,
                "total_incomes": total_incomes
            },
            "monthly": {
                "expenses_sum": float(monthly_expenses),
                "incomes_confirmed": float(monthly_incomes_confirmed),
                "incomes_pending": float(monthly_incomes_pending),
                "incomes_sum": float(monthly_incomes_confirmed + monthly_incomes_pending),
                "net": float(monthly_incomes_confirmed - monthly_expenses)
            },
            "recent_activity": {
                "expenses_week": recent_expenses,
                "incomes_week": recent_incomes
            },
            "timestamp": datetime.now().isoformat(),
            "month": current_month.strftime("%Y-%m")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")

@router.get("/health")
def realtime_health():
    """Health check para APIs de tiempo real"""
    return {
        "status": "ok",
        "module": "realtime_api",
        "endpoints": [
            "/api/realtime/incomes - Ingresos con info completa",
            "/api/realtime/expenses - Gastos con info completa",
            "/api/realtime/apartments - Apartamentos con estadísticas",
            "/api/realtime/dashboard-stats - Stats optimizadas"
        ],
        "features": [
            "real_time_updates",
            "complete_data_response", 
            "optimized_queries",
            "timestamp_tracking"
        ]
    }