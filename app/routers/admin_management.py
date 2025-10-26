# app/routers/admin_management.py
"""
Panel de administración completo para gestionar apartamentos, gastos e ingresos
"""
from __future__ import annotations
import os
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import date, datetime

from ..db import get_db
from .. import models, schemas

# Initialize templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

router = APIRouter(prefix="/admin/manage", tags=["admin-management"])

def require_admin_key(
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
    key: str | None = Query(default=None),
):
    admin = os.getenv("ADMIN_KEY", "")
    provided = x_internal_key or key
    if not admin or provided != admin:
        raise HTTPException(status_code=403, detail="Forbidden - Admin key required")

# ============ PÁGINAS PRINCIPALES ============

@router.get("/", response_class=HTMLResponse)
def admin_management_home(request: Request):
    """Panel principal de administración"""
    return templates.TemplateResponse("admin_management.html", {"request": request})

@router.get("/apartments", response_class=HTMLResponse)
def apartments_management_page(request: Request, db: Session = Depends(get_db)):
    """Página de gestión de apartamentos"""
    apartments = db.query(models.Apartment).order_by(desc(models.Apartment.created_at)).all()
    return templates.TemplateResponse("admin_apartments_management.html", {
        "request": request,
        "apartments": apartments
    })

@router.get("/expenses", response_class=HTMLResponse)
def expenses_management_page(
    request: Request, 
    apartment_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Página de gestión de gastos"""
    # Obtener apartamentos para el selector
    apartments = db.query(models.Apartment).filter(models.Apartment.is_active == True).all()
    
    # Obtener gastos (filtrados si se especifica apartamento)
    expenses_query = db.query(models.Expense).join(models.Apartment)
    if apartment_id:
        expenses_query = expenses_query.filter(models.Expense.apartment_id == apartment_id)
    
    expenses = expenses_query.order_by(desc(models.Expense.date)).limit(100).all()
    
    # Obtener apartamento seleccionado
    selected_apartment = None
    if apartment_id:
        selected_apartment = db.query(models.Apartment).filter(models.Apartment.id == apartment_id).first()
    
    return templates.TemplateResponse("admin_expenses_management.html", {
        "request": request,
        "expenses": expenses,
        "apartments": apartments,
        "selected_apartment": selected_apartment,
        "apartment_id": apartment_id
    })

@router.get("/incomes", response_class=HTMLResponse)
def incomes_management_page(
    request: Request,
    apartment_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Página de gestión de ingresos"""
    # Obtener apartamentos para el selector
    apartments = db.query(models.Apartment).filter(models.Apartment.is_active == True).all()
    
    # Obtener ingresos (filtrados)
    incomes_query = db.query(models.Income).join(models.Apartment)
    if apartment_id:
        incomes_query = incomes_query.filter(models.Income.apartment_id == apartment_id)
    if status:
        incomes_query = incomes_query.filter(models.Income.status == status)
    
    incomes = incomes_query.order_by(desc(models.Income.date)).limit(100).all()
    
    # Obtener apartamento seleccionado
    selected_apartment = None
    if apartment_id:
        selected_apartment = db.query(models.Apartment).filter(models.Apartment.id == apartment_id).first()
    
    return templates.TemplateResponse("admin_incomes_management.html", {
        "request": request,
        "incomes": incomes,
        "apartments": apartments,
        "selected_apartment": selected_apartment,
        "apartment_id": apartment_id,
        "status": status
    })

# ============ API ENDPOINTS PARA ADMINISTRACIÓN ============

@router.get("/api/apartments")
def api_list_apartments(db: Session = Depends(get_db), _: None = Depends(require_admin_key)):
    """API: Listar apartamentos para administración"""
    apartments = db.query(models.Apartment).order_by(desc(models.Apartment.created_at)).all()
    return {
        "apartments": [
            {
                "id": apt.id,
                "code": apt.code,
                "name": apt.name,
                "owner_email": apt.owner_email,
                "is_active": apt.is_active,
                "created_at": apt.created_at.isoformat() if apt.created_at else None
            }
            for apt in apartments
        ],
        "total": len(apartments)
    }

@router.post("/api/apartments")
def api_create_apartment(
    code: str = Form(...),
    name: str = Form(...),
    owner_email: str = Form(...),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key)
):
    """API: Crear apartamento"""
    # Verificar si ya existe
    existing = db.query(models.Apartment).filter(models.Apartment.code == code.upper().strip()).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"El apartamento {code} ya existe")
    
    apartment = models.Apartment(
        code=code.upper().strip(),
        name=name.strip(),
        owner_email=owner_email.lower().strip(),
        is_active=True
    )
    
    try:
        db.add(apartment)
        db.commit()
        db.refresh(apartment)
        return {
            "success": True,
            "message": f"Apartamento {code} creado exitosamente",
            "apartment": {
                "id": apartment.id,
                "code": apartment.code,
                "name": apartment.name,
                "owner_email": apartment.owner_email
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creando apartamento: {str(e)}")

@router.put("/api/apartments/{apartment_id}")
def api_update_apartment(
    apartment_id: str,
    name: str = Form(...),
    owner_email: str = Form(...),
    is_active: bool = Form(...),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key)
):
    """API: Actualizar apartamento"""
    apartment = db.query(models.Apartment).filter(models.Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    
    apartment.name = name.strip()
    apartment.owner_email = owner_email.lower().strip()
    apartment.is_active = is_active
    
    try:
        db.commit()
        db.refresh(apartment)
        return {
            "success": True,
            "message": "Apartamento actualizado exitosamente",
            "apartment": {
                "id": apartment.id,
                "code": apartment.code,
                "name": apartment.name,
                "owner_email": apartment.owner_email,
                "is_active": apartment.is_active
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error actualizando apartamento: {str(e)}")

@router.delete("/api/apartments/{apartment_id}")
def api_delete_apartment(
    apartment_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key)
):
    """API: Eliminar apartamento"""
    apartment = db.query(models.Apartment).filter(models.Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    
    # Verificar si tiene gastos o ingresos asociados
    expenses_count = db.query(models.Expense).filter(models.Expense.apartment_id == apartment_id).count()
    incomes_count = db.query(models.Income).filter(models.Income.apartment_id == apartment_id).count()
    
    if expenses_count > 0 or incomes_count > 0:
        return {
            "success": False,
            "message": f"No se puede eliminar: tiene {expenses_count} gastos y {incomes_count} ingresos asociados",
            "can_delete": False,
            "expenses_count": expenses_count,
            "incomes_count": incomes_count
        }
    
    try:
        apartment_info = {"code": apartment.code, "name": apartment.name}
        db.delete(apartment)
        db.commit()
        return {
            "success": True,
            "message": f"Apartamento {apartment_info['code']} eliminado exitosamente",
            "deleted_apartment": apartment_info
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error eliminando apartamento: {str(e)}")

# ============ GESTIÓN DE GASTOS ============

@router.post("/api/expenses")
def api_create_expense(
    apartment_id: str = Form(...),
    date: date = Form(...),
    amount_gross: float = Form(...),
    currency: str = Form("EUR"),
    category: str = Form(...),
    description: str = Form(""),
    vendor: str = Form(""),
    invoice_number: str = Form(""),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key)
):
    """API: Crear gasto"""
    # Verificar apartamento
    apartment = db.query(models.Apartment).filter(models.Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    
    expense = models.Expense(
        apartment_id=apartment_id,
        date=date,
        amount_gross=amount_gross,
        currency=currency,
        category=category,
        description=description,
        vendor=vendor,
        invoice_number=invoice_number,
        source="admin_manual"
    )
    
    try:
        db.add(expense)
        db.commit()
        db.refresh(expense)
        return {
            "success": True,
            "message": "Gasto creado exitosamente",
            "expense": {
                "id": expense.id,
                "apartment_code": apartment.code,
                "date": str(expense.date),
                "amount_gross": float(expense.amount_gross),
                "category": expense.category,
                "vendor": expense.vendor
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creando gasto: {str(e)}")

@router.delete("/api/expenses/{expense_id}")
def api_delete_expense(
    expense_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key)
):
    """API: Eliminar gasto"""
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    
    try:
        expense_info = {
            "id": expense.id,
            "date": str(expense.date),
            "amount_gross": float(expense.amount_gross),
            "description": expense.description,
            "vendor": expense.vendor
        }
        db.delete(expense)
        db.commit()
        return {
            "success": True,
            "message": "Gasto eliminado exitosamente",
            "deleted_expense": expense_info
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error eliminando gasto: {str(e)}")

# ============ GESTIÓN DE INGRESOS ============

@router.post("/api/incomes")
def api_create_income(
    apartment_id: str = Form(...),
    date: date = Form(...),
    amount_gross: float = Form(...),
    currency: str = Form("EUR"),
    status: str = Form("CONFIRMED"),
    guest_name: str = Form(""),
    guest_email: str = Form(""),
    booking_reference: str = Form(""),
    check_in_date: Optional[date] = Form(None),
    check_out_date: Optional[date] = Form(None),
    guests_count: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key)
):
    """API: Crear ingreso"""
    # Verificar apartamento
    apartment = db.query(models.Apartment).filter(models.Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    
    income = models.Income(
        apartment_id=apartment_id,
        date=date,
        amount_gross=amount_gross,
        currency=currency,
        status=status,
        source="admin_manual",
        guest_name=guest_name,
        guest_email=guest_email,
        booking_reference=booking_reference,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        guests_count=guests_count
    )
    
    try:
        db.add(income)
        db.commit()
        db.refresh(income)
        return {
            "success": True,
            "message": "Ingreso creado exitosamente",
            "income": {
                "id": str(income.id),
                "apartment_code": apartment.code,
                "date": str(income.date),
                "amount_gross": float(income.amount_gross),
                "status": income.status,
                "guest_name": income.guest_name
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creando ingreso: {str(e)}")

@router.delete("/api/incomes/{income_id}")
def api_delete_income(
    income_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key)
):
    """API: Eliminar ingreso"""
    income = db.query(models.Income).filter(models.Income.id == income_id).first()
    if not income:
        raise HTTPException(status_code=404, detail="Ingreso no encontrado")
    
    try:
        income_info = {
            "id": str(income.id),
            "date": str(income.date),
            "amount_gross": float(income.amount_gross),
            "status": income.status,
            "guest_name": income.guest_name
        }
        db.delete(income)
        db.commit()
        return {
            "success": True,
            "message": "Ingreso eliminado exitosamente",
            "deleted_income": income_info
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error eliminando ingreso: {str(e)}")

@router.patch("/api/incomes/{income_id}/status")
def api_update_income_status(
    income_id: str,
    status: str = Form(...),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key)
):
    """API: Cambiar estado de ingreso"""
    income = db.query(models.Income).filter(models.Income.id == income_id).first()
    if not income:
        raise HTTPException(status_code=404, detail="Ingreso no encontrado")
    
    if status not in ["PENDING", "CONFIRMED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="Estado inválido")
    
    old_status = income.status
    income.status = status
    
    try:
        db.commit()
        db.refresh(income)
        return {
            "success": True,
            "message": f"Estado cambiado de {old_status} a {status}",
            "income": {
                "id": str(income.id),
                "old_status": old_status,
                "new_status": income.status,
                "guest_name": income.guest_name,
                "amount_gross": float(income.amount_gross)
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error actualizando estado: {str(e)}")

# ============ ESTADÍSTICAS RÁPIDAS ============

@router.get("/api/stats")
def api_admin_stats(db: Session = Depends(get_db), _: None = Depends(require_admin_key)):
    """API: Estadísticas rápidas para el panel de admin"""
    
    # Contar totales
    total_apartments = db.query(models.Apartment).count()
    active_apartments = db.query(models.Apartment).filter(models.Apartment.is_active == True).count()
    total_expenses = db.query(models.Expense).count()
    total_incomes = db.query(models.Income).count()
    
    # Sumas del mes actual
    current_month = datetime.now().replace(day=1).date()
    monthly_expenses = db.query(models.Expense).filter(models.Expense.date >= current_month).all()
    monthly_incomes = db.query(models.Income).filter(models.Income.date >= current_month).all()
    
    monthly_expenses_sum = sum(float(exp.amount_gross) for exp in monthly_expenses)
    monthly_incomes_sum = sum(float(inc.amount_gross) for inc in monthly_incomes if inc.status != "CANCELLED")
    
    # Ingresos por estado
    pending_incomes = db.query(models.Income).filter(models.Income.status == "PENDING").count()
    confirmed_incomes = db.query(models.Income).filter(models.Income.status == "CONFIRMED").count()
    
    return {
        "totals": {
            "apartments": total_apartments,
            "active_apartments": active_apartments,
            "expenses": total_expenses,
            "incomes": total_incomes
        },
        "monthly": {
            "expenses_sum": monthly_expenses_sum,
            "incomes_sum": monthly_incomes_sum,
            "net": monthly_incomes_sum - monthly_expenses_sum,
            "expenses_count": len(monthly_expenses),
            "incomes_count": len(monthly_incomes)
        },
        "incomes_by_status": {
            "pending": pending_incomes,
            "confirmed": confirmed_incomes
        }
    }