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
        with engine.connect() as conn:
            conn.execute("SELECT 1")
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
