from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from .db import Base, engine
from . import models
from .routers import reservations
from .routers import admin

app = FastAPI(title="OPS Core (DINERO)")

try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"[init] DB init skipped: {e}")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/")
def root():
    return RedirectResponse(url="/docs")

app.include_router(reservations.router)
app.include_router(admin.router)