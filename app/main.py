# app/main.py
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from .routers import reservations, expenses, admin, apartments

# Asegúrate de importar modelos ANTES de create_all()
from . import models  # noqa: F401  (necesario para que SQLAlchemy conozca las tablas)

from .db import Base, engine
from .routers import reservations, expenses, admin

app = FastAPI(title="SES.GASTOS")

# Crear tablas al arrancar (si faltan)
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

@app.get("/")
def root():
    return RedirectResponse(url="/docs")

# Routers (registrados una sola vez)
app.include_router(reservations.router)
app.include_router(expenses.router)
app.include_router(apartments.router)
app.include_router(admin.router)
