# app/main.py
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

# importa modelos antes de create_all para que SQLAlchemy “conozca” las tablas
from . import models  # noqa: F401
from .db import Base, engine

# routers
from .routers import reservations, expenses, apartments, admin

app = FastAPI(title="SES.GASTOS")

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

# registra routers una sola vez
app.include_router(reservations.router)
app.include_router(expenses.router)
app.include_router(apartments.router)
app.include_router(admin.router)
