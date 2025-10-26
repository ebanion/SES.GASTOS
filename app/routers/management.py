# app/routers/management.py
"""
Router para la interfaz web de gestión
"""
from __future__ import annotations
import os
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models

# Initialize templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

router = APIRouter(prefix="/management", tags=["management"])

@router.get("/", response_class=HTMLResponse)
def management_dashboard(request: Request, db: Session = Depends(get_db)):
    """Interfaz web de gestión principal"""
    
    # Obtener estadísticas básicas
    total_apartments = db.query(models.Apartment).count()
    total_expenses = db.query(models.Expense).count()
    total_incomes = db.query(models.Income).count()
    
    # Obtener apartamentos activos para los selects
    active_apartments = db.query(models.Apartment).filter(
        models.Apartment.is_active == True
    ).all()
    
    return templates.TemplateResponse("management_dashboard.html", {
        "request": request,
        "total_apartments": total_apartments,
        "total_expenses": total_expenses,
        "total_incomes": total_incomes,
        "active_apartments": active_apartments
    })

@router.get("/health")
def management_health():
    """Health check para el módulo de gestión"""
    return {
        "status": "ok",
        "module": "management",
        "features": [
            "apartments_crud",
            "expenses_crud", 
            "incomes_crud",
            "dashboard_stats"
        ]
    }