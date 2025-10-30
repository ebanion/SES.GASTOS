"""
Router de Analytics Financieros y Fiscales
KPIs hoteleros, salud financiera, predicciones e impuestos
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

from ..db import get_db
from ..models import AccountUser, User, Account
from ..schemas import (
    KPIsOut, FinancialHealthOut, YearOverYearOut, ExpenseCategoryAnalysis,
    QuarterlyIVAOut, QuarterlyIRPFOut, FiscalAlertOut, TaxScenarioOut
)
from ..services.financial_analytics import FinancialAnalytics
from ..services.fiscal_calculator import FiscalCalculator

# Sistema de autenticación multiusuario
from ..auth_multiuser import get_current_user, get_current_account

# Templates
templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="/analytics", tags=["Analytics Financieros"])


# Helper: obtener account_id del usuario actual
def get_user_account_id(user: User, db: Session) -> str:
    """Obtiene el account_id del usuario actual (primera cuenta disponible)"""
    account_user = db.query(AccountUser).filter(AccountUser.user_id == user.id).first()
    if not account_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario sin cuenta asignada"
        )
    return account_user.account_id


# ==================== FRONTEND ====================

@router.get("/", response_class=HTMLResponse)
async def analytics_dashboard_page(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Renderiza el dashboard de analytics (frontend estándar)
    """
    return templates.TemplateResponse(
        "analytics_dashboard.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.get("/pro", response_class=HTMLResponse)
async def analytics_dashboard_pro_page(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Renderiza el dashboard de analytics AVANZADO (Power BI-style)
    Versión PRO con visualizaciones profesionales y UX mejorada
    """
    return templates.TemplateResponse(
        "analytics_advanced.html",
        {
            "request": request,
            "user": current_user
        }
    )


# ==================== DEMO PÚBLICO (Sin autenticación) ====================

@router.get("/demo", response_class=HTMLResponse)
async def analytics_demo_page(request: Request):
    """
    DEMO PÚBLICO del dashboard de analytics (sin autenticación)
    Versión de prueba con datos de ejemplo
    """
    return templates.TemplateResponse(
        "analytics_dashboard.html",
        {
            "request": request,
            "user": None
        }
    )


@router.get("/demo/pro", response_class=HTMLResponse)
async def analytics_demo_pro_page(request: Request):
    """
    DEMO PÚBLICO del dashboard PRO (sin autenticación)
    Versión de prueba con datos de ejemplo
    """
    return templates.TemplateResponse(
        "analytics_advanced.html",
        {
            "request": request,
            "user": None
        }
    )


@router.get("/demo/dashboard")
async def analytics_demo_dashboard():
    """
    DEMO: Dashboard integrado con datos de ejemplo
    """
    from datetime import datetime, timedelta
    
    return {
        "period": {
            "label": f"{datetime.now().strftime('%B %Y')}",
            "start_date": (datetime.now().replace(day=1)).isoformat(),
            "end_date": datetime.now().isoformat()
        },
        "financial_health": {
            "score": 85,
            "status": "green",
            "message": "Tu negocio está en un punto óptimo con márgenes saludables y ocupación superior al 75%",
            "margin_percent": 42.3,
            "occupancy_rate": 78.5,
            "expense_ratio": 32.1,
            "net_profit": 2430.00,
            "total_income": 5400.00,
            "total_expenses": 2970.00
        },
        "kpis": {
            "adr": 142.50,
            "occupancy_rate": 78.5,
            "revpar": 111.86,
            "total_reservations": 18,
            "nights_occupied": 38,
            "nights_available": 48
        },
        "income_comparison": {
            "current_month": 5400.00,
            "previous_month": 4800.00,
            "change_amount": 600.00,
            "change_percent": 12.5
        },
        "alerts": [
            {
                "title": "Vencimiento IVA próximo",
                "message": "Modelo 303 vence en 8 días: 20 de enero",
                "severity": "warning",
                "icon": "⚠️",
                "due_date": (datetime.now() + timedelta(days=8)).isoformat()
            },
            {
                "title": "Umbral de IVA deducible",
                "message": "Has superado el 80% del límite trimestral",
                "severity": "info",
                "icon": "💰",
                "due_date": None
            },
            {
                "title": "Gastos sin categorizar",
                "message": "12 transacciones pendientes de categorizar",
                "severity": "warning",
                "icon": "📊",
                "due_date": None
            }
        ]
    }


@router.get("/demo/expense-analysis")
async def analytics_demo_expenses():
    """
    DEMO: Análisis de gastos con datos de ejemplo
    """
    return [
        {
            "category": "Limpieza",
            "total_amount": 648.00,
            "percent_of_income": 12.0,
            "benchmark_percent": 10.0,
            "status": "optimal",
            "recommendation": "Tu gasto en limpieza está dentro del rango óptimo del sector (10-15%)",
            "transaction_count": 32
        },
        {
            "category": "Mantenimiento",
            "total_amount": 432.00,
            "percent_of_income": 8.0,
            "benchmark_percent": 6.0,
            "status": "high",
            "recommendation": "Tu gasto en mantenimiento es alto. Considera negociar contratos o buscar alternativas",
            "transaction_count": 18
        },
        {
            "category": "Suministros",
            "total_amount": 594.00,
            "percent_of_income": 11.0,
            "benchmark_percent": 9.0,
            "status": "very_high",
            "recommendation": "Gastos en suministros exceden el benchmark. Optimiza consumo energético y revisa tarifas",
            "transaction_count": 45
        },
        {
            "category": "Marketing",
            "total_amount": 270.00,
            "percent_of_income": 5.0,
            "benchmark_percent": 7.0,
            "status": "optimal",
            "recommendation": "Gasto en marketing está optimizado. Considera aumentar si buscas más visibilidad",
            "transaction_count": 8
        }
    ]


@router.get("/demo/fiscal/simulate")
async def analytics_demo_fiscal_simulate():
    """
    DEMO: Simulador fiscal con datos de ejemplo
    """
    return {
        "projected_annual_income": 60000.00,
        "projected_annual_expenses": 30000.00,
        "projected_net_income": 30000.00,
        "scenarios": {
            "autonomo_general": {
                "name": "Autónomo Régimen General",
                "irpf": 4800.00,
                "seguridad_social": 4560.00,
                "total_tax": 9360.00,
                "net_after_tax": 20640.00,
                "effective_rate": 31.2,
                "recommended": False,
                "note": "Alta carga fiscal para este nivel de ingresos"
            },
            "sociedad_limitada": {
                "name": "Sociedad Limitada (SL)",
                "impuesto_sociedades": 3450.00,
                "seguridad_social": 4200.00,
                "total_tax": 7650.00,
                "net_after_tax": 22350.00,
                "effective_rate": 25.5,
                "recommended": True,
                "note": "Régimen más eficiente para este volumen de negocio"
            },
            "modulos": {
                "name": "Módulos",
                "cuota_fija": 5200.00,
                "iva": 2100.00,
                "total_tax": 7300.00,
                "net_after_tax": 22700.00,
                "effective_rate": 24.3,
                "recommended": False,
                "note": "Cuota fija puede ser interesante si calificas"
            }
        },
        "recommendation": "Para tu nivel de ingresos (€60,000), la Sociedad Limitada es más eficiente fiscalmente que el régimen de autónomo general, con un ahorro estimado de €1,710 anuales."
    }


# ==================== KPIs HOTELEROS ====================

@router.get("/kpis", response_model=KPIsOut)
def get_kpis(
    apartment_id: Optional[str] = None,
    start_date: Optional[date] = Query(None, description="Fecha inicio periodo (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Fecha fin periodo (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene KPIs hoteleros principales: ADR, Ocupación, RevPAR
    
    - **ADR**: Average Daily Rate (precio medio por noche ocupada)
    - **Ocupación**: % de noches ocupadas sobre disponibles
    - **RevPAR**: Revenue Per Available Room (ingreso por habitación disponible)
    """
    analytics = FinancialAnalytics(db)
    account_id = get_user_account_id(current_user, db)
    
    # Si no se especifica periodo, usar mes actual
    if not start_date or not end_date:
        today = date.today()
        start_date = today.replace(day=1)
        import calendar
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = today.replace(day=last_day)
    
    adr = analytics.calculate_adr(account_id, apartment_id, start_date, end_date)
    occupancy = analytics.calculate_occupancy_rate(account_id, apartment_id, start_date, end_date)
    revpar = analytics.calculate_revpar(account_id, apartment_id, start_date, end_date)
    
    return KPIsOut(
        adr=float(adr),
        occupancy_rate=float(occupancy),
        revpar=float(revpar),
        period_start=start_date.isoformat(),
        period_end=end_date.isoformat(),
        apartment_id=apartment_id
    )


@router.get("/financial-health", response_model=FinancialHealthOut)
def get_financial_health(
    period_months: int = Query(1, ge=1, le=12, description="Meses a analizar"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Estado de salud financiera con semáforo (Verde/Amarillo/Rojo)
    
    Analiza:
    - Margen de beneficio
    - Tasa de ocupación
    - Control de gastos
    
    Devuelve status, score (0-100) y mensaje explicativo.
    """
    analytics = FinancialAnalytics(db)
    health_data = analytics.calculate_financial_health(
        account_id=get_user_account_id(current_user, db),
        period_months=period_months
    )
    
    return FinancialHealthOut(**health_data)


@router.get("/year-over-year", response_model=YearOverYearOut)
def get_year_over_year(
    start_date: date = Query(..., description="Fecha inicio periodo actual"),
    end_date: date = Query(..., description="Fecha fin periodo actual"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Comparativa año actual vs año anterior
    
    Compara mismo periodo del año anterior:
    - Ingresos, gastos, beneficio
    - Ocupación, ADR
    - Variaciones porcentuales
    """
    analytics = FinancialAnalytics(db)
    comparison = analytics.compare_year_over_year(
        account_id=get_user_account_id(current_user, db),
        current_start=start_date,
        current_end=end_date
    )
    
    return YearOverYearOut(**comparison)


@router.get("/expense-analysis", response_model=List[ExpenseCategoryAnalysis])
def get_expense_analysis(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Análisis de gastos por categoría con benchmarking
    
    Para cada categoría muestra:
    - Total gastado y % sobre ingresos
    - Comparación con benchmark del sector
    - Estado (óptimo/alto/muy alto)
    - Recomendaciones específicas
    """
    analytics = FinancialAnalytics(db)
    analysis = analytics.analyze_expense_categories(
        account_id=get_user_account_id(current_user, db),
        start_date=start_date,
        end_date=end_date
    )
    
    return [ExpenseCategoryAnalysis(**item) for item in analysis]


# ==================== FISCAL ====================

@router.get("/fiscal/iva/{year}/{quarter}", response_model=QuarterlyIVAOut)
def calculate_quarterly_iva(
    year: int = Query(..., ge=2020, le=2030),
    quarter: int = Query(..., ge=1, le=4, description="Trimestre (1-4)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calcula IVA trimestral (Modelo 303)
    
    - IVA repercutido (cobrado)
    - IVA soportado (pagado en gastos)
    - IVA a ingresar
    - Fecha límite de presentación
    """
    calculator = FiscalCalculator(db)
    iva_data = calculator.calculate_quarterly_iva(
        account_id=get_user_account_id(current_user, db),
        year=year,
        quarter=quarter
    )
    
    return QuarterlyIVAOut(**iva_data)


@router.get("/fiscal/irpf/{year}/{quarter}", response_model=QuarterlyIRPFOut)
def calculate_quarterly_irpf(
    year: int = Query(..., ge=2020, le=2030),
    quarter: int = Query(..., ge=1, le=4),
    regime: str = Query("general", regex="^(general|modules)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calcula IRPF trimestral (Modelo 130)
    
    - Rendimiento neto
    - IRPF calculado según régimen
    - Pago fraccionado del trimestre
    - Fecha límite
    """
    calculator = FiscalCalculator(db)
    irpf_data = calculator.calculate_quarterly_irpf(
        account_id=get_user_account_id(current_user, db),
        year=year,
        quarter=quarter,
        regime=regime
    )
    
    return QuarterlyIRPFOut(**irpf_data)


@router.get("/fiscal/alerts", response_model=List[FiscalAlertOut])
def get_fiscal_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Alertas fiscales proactivas
    
    Notifica sobre:
    - Vencimientos próximos (IVA, IRPF)
    - Umbrales de facturación
    - Gastos sin categorizar
    - Oportunidades de optimización
    """
    calculator = FiscalCalculator(db)
    alerts = calculator.get_fiscal_alerts(
        account_id=get_user_account_id(current_user, db)
    )
    
    return [FiscalAlertOut(**alert) for alert in alerts]


@router.post("/fiscal/simulate", response_model=TaxScenarioOut)
def simulate_tax_scenarios(
    projected_annual_income: float = Query(..., gt=0, description="Ingresos proyectados anuales"),
    projected_annual_expenses: float = Query(..., ge=0, description="Gastos proyectados anuales"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Simulador fiscal: Compara regímenes fiscales
    
    Escenarios:
    - Autónomo régimen general
    - Sociedad Limitada (SL)
    - Módulos (estimación objetiva)
    
    Muestra impuestos totales y neto después de impuestos.
    """
    calculator = FiscalCalculator(db)
    simulation = calculator.simulate_tax_scenarios(
        account_id=get_user_account_id(current_user, db),
        projected_annual_income=Decimal(str(projected_annual_income)),
        projected_annual_expenses=Decimal(str(projected_annual_expenses))
    )
    
    return TaxScenarioOut(**simulation)


# ==================== DASHBOARD INTEGRADO ====================

@router.get("/dashboard")
def get_analytics_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Dashboard unificado con todas las métricas clave
    
    Devuelve:
    - KPIs principales
    - Salud financiera
    - Alertas fiscales activas
    - Comparativa mes actual vs anterior
    """
    analytics = FinancialAnalytics(db)
    calculator = FiscalCalculator(db)
    account_id = get_user_account_id(current_user, db)
    
    # Periodo: mes actual
    today = date.today()
    import calendar
    start_current = today.replace(day=1)
    last_day = calendar.monthrange(today.year, today.month)[1]
    end_current = today.replace(day=last_day)
    
    # KPIs
    adr = analytics.calculate_adr(account_id, None, start_current, end_current)
    occupancy = analytics.calculate_occupancy_rate(account_id, None, start_current, end_current)
    revpar = analytics.calculate_revpar(account_id, None, start_current, end_current)
    
    # Salud financiera
    health = analytics.calculate_financial_health(account_id, period_months=1)
    
    # Alertas fiscales
    alerts = calculator.get_fiscal_alerts(account_id)
    
    # Comparativa con mes anterior
    # Calcular mes anterior
    if today.month == 1:
        start_previous = date(today.year - 1, 12, 1)
        end_previous = date(today.year - 1, 12, 31)
    else:
        start_previous = date(today.year, today.month - 1, 1)
        last_day_prev = calendar.monthrange(today.year, today.month - 1)[1]
        end_previous = date(today.year, today.month - 1, last_day_prev)
    
    income_current = analytics._get_total_income(account_id, start_current, end_current)
    income_previous = analytics._get_total_income(account_id, start_previous, end_previous)
    
    income_change = 0.0
    if income_previous > 0:
        income_change = float(((income_current - income_previous) / income_previous) * 100)
    
    return {
        "period": {
            "start_date": start_current.isoformat(),
            "end_date": end_current.isoformat(),
            "label": f"{today.strftime('%B %Y')}"
        },
        "kpis": {
            "adr": float(adr),
            "occupancy_rate": float(occupancy),
            "revpar": float(revpar)
        },
        "financial_health": health,
        "alerts": alerts,
        "income_comparison": {
            "current_month": float(income_current),
            "previous_month": float(income_previous),
            "change_percent": income_change
        }
    }
