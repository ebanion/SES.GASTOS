from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..db import get_db
import os

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/db-ping")
def db_ping(key: str, db: Session = Depends(get_db)):
    if key != os.getenv("ADMIN_KEY"):
        raise HTTPException(status_code=403, detail="forbidden")
    try:
        db.execute(text("select 1"))
        return {"db": "ok"}
    except Exception as e:
        return {"db": "error", "detail": str(e)}
