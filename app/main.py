from fastapi import FastAPI
from .db import Base, engine

app = FastAPI(title="OPS Core (DINERO)")

# Crear tablas si hay modelos cargados; no fallar si la DB no está lista aún
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"[init] DB init skipped: {e}")

@app.get("/health")
def health():
    return {"ok": True}
