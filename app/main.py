# app/main.py
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

# Importa modelos para que SQLAlchemy “conozca” las tablas
from . import models  # noqa

from .db import Base, engine

# Routers
from .routers import reservations, expenses, apartments, incomes, admin, incomes

# Dashboard
from .dashboard_api import router as dashboard_router

# Vectors
from .routers import vectors



app = FastAPI(title="SES.GASTOS")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Crear/migrar tablas al arrancar
@app.on_event("startup")
def on_startup() -> None:
    try:
        Base.metadata.create_all(bind=engine)
        print("[startup] DB ready")
    except Exception as e:
        print(f"[startup] create_all failed: {e}")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/db-status")
def db_status():
    """Check database connection status"""
    try:
        from app.db import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"database": "connected", "status": "ok"}
    except Exception as e:
        return {"database": "disconnected", "error": str(e), "status": "error"}

@app.get("/")
def root():
    return RedirectResponse(url="/dashboard")

@app.get("/dashboard")
def dashboard_redirect():
    return RedirectResponse(url="/api/v1/dashboard/")

# Montar routers (orden no crítico, pero admin al final está bien)
app.include_router(reservations.router)
app.include_router(expenses.router)
app.include_router(apartments.router)
app.include_router(incomes.router)   # <= IMPORTANTE
app.include_router(admin.router)
app.include_router(dashboard_router)
app.include_router(vectors.router)

# Pequeño debug para ver rutas en producción si hace falta
@app.get("/debug/routes")
def list_routes():
    return sorted([getattr(r, "path", "") for r in app.router.routes])

@app.post("/init-demo-data")
def init_demo_data():
    """TEMPORAL: Inicializar datos de demostración (ELIMINAR EN PRODUCCIÓN)"""
    from .db import SessionLocal
    from . import models
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    try:
        # Verificar si ya hay apartamentos
        existing_apartments = db.query(models.Apartment).count()
        if existing_apartments > 0:
            return {"message": f"Ya hay {existing_apartments} apartamentos", "apartments": existing_apartments}
        
        # Crear apartamentos
        apartments_data = [
            {"code": "SES01", "name": "Apartamento Centro", "owner_email": "demo@sesgas.com"},
            {"code": "SES02", "name": "Apartamento Playa", "owner_email": "demo@sesgas.com"},
            {"code": "SES03", "name": "Apartamento Montaña", "owner_email": "demo@sesgas.com"}
        ]
        
        created_apartments = []
        for apt_data in apartments_data:
            apt = models.Apartment(
                code=apt_data["code"],
                name=apt_data["name"],
                owner_email=apt_data["owner_email"],
                is_active=True
            )
            db.add(apt)
            created_apartments.append(apt)
        
        db.commit()
        
        # Refresh para obtener IDs
        for apt in created_apartments:
            db.refresh(apt)
        
        # Crear algunos gastos de demo
        base_date = datetime.now() - timedelta(days=15)
        expenses_data = [
            {"amount": 45.50, "category": "Restauración", "vendor": "Restaurante Demo", "description": "Gasto de demostración"},
            {"amount": 25.00, "category": "Transporte", "vendor": "Taxi Demo", "description": "Traslado demo"},
            {"amount": 80.00, "category": "Servicios", "vendor": "Servicio Demo", "description": "Reparación demo"}
        ]
        
        created_expenses = []
        for i, exp_data in enumerate(expenses_data):
            apartment = created_apartments[i % len(created_apartments)]
            
            expense = models.Expense(
                apartment_id=apartment.id,
                date=(base_date + timedelta(days=i*2)).date(),
                amount_gross=exp_data["amount"],
                currency="EUR",
                category=exp_data["category"],
                description=exp_data["description"],
                vendor=exp_data["vendor"],
                source="demo_init"
            )
            db.add(expense)
            created_expenses.append(expense)
        
        # Crear algunos ingresos de demo
        incomes_data = [
            {"amount": 150.00, "status": "CONFIRMED"},
            {"amount": 200.00, "status": "CONFIRMED"},
            {"amount": 180.00, "status": "PENDING"}
        ]
        
        created_incomes = []
        for i, inc_data in enumerate(incomes_data):
            apartment = created_apartments[i % len(created_apartments)]
            
            income = models.Income(
                apartment_id=apartment.id,
                date=(base_date + timedelta(days=i*3)).date(),
                amount_gross=inc_data["amount"],
                currency="EUR",
                status=inc_data["status"],
                source="demo_init"
            )
            db.add(income)
            created_incomes.append(income)
        
        db.commit()
        
        return {
            "success": True,
            "message": "Datos de demostración creados",
            "apartments": len(created_apartments),
            "expenses": len(created_expenses),
            "incomes": len(created_incomes),
            "apartment_codes": [apt.code for apt in created_apartments],
            "next_steps": [
                "1. Ejecuta el bot: python app/bot/Telegram_expense_bot.py",
                "2. En Telegram: /start",
                "3. Configura apartamento: /usar SES01",
                "4. Envía foto de factura",
                "5. Ve el dashboard: /api/v1/dashboard/"
            ]
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()
