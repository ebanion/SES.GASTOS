# app/main_simple.py - Versión mínima para debugging
from fastapi import FastAPI

app = FastAPI(title="SES.GASTOS Simple")

@app.get("/")
def root():
    return {"message": "Simple version working", "status": "ok"}

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/test")
def test():
    return {"test": "working", "version": "simple"}

# Solo endpoints básicos para verificar que FastAPI funciona