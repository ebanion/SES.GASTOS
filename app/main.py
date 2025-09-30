from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from .db import Base, engine
from . import models
from .routers import reservations, admin

app = FastAPI(title="OPS Core (DINERO)")

@app.on_event("startup")
def ensure_db():
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

app.include_router(reservations.router)
app.include_router(admin.router)
