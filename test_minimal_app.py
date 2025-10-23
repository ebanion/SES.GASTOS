#!/usr/bin/env python3
"""
Aplicación mínima para probar que FastAPI funciona
"""

from fastapi import FastAPI

app = FastAPI(title="Test Minimal")

@app.get("/")
def root():
    return {"message": "Minimal app working", "status": "ok"}

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/test")
def test():
    return {"test": "working", "timestamp": "2024-12-22"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)