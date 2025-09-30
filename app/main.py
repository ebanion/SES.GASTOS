# app/main.py
from fastapi import FastAPI
from .db import Base, engine
from . import models              # <-- importa modelos para create_all
from .routers import reservations # <-- importa el router

app = FastAPI(title="OPS Core (DINERO)")

try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"[init] DB init skipped: {e}")

@app.get("/health")
def health():
    return {"ok": True}

# monta el router bajo /api/v1/r
