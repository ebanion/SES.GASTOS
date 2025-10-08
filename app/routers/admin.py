# app/routers/admin.py
from __future__ import annotations

import os
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect

from ..db import engine, get_db
from .. import models  # asegura modelos cargados
from ..db import Base

router = APIRouter(tags=["admin"])

@router.get("/admin/db-ping")
def db_ping(key: str = Query(...), db: Session = Depends(get_db)):
    if key != os.getenv("ADMIN_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden")
    insp = inspect(engine)
    tables = sorted(insp.get_table_names())
    return {"ok": True, "tables": tables}

@router.post("/admin/init")
def admin_init(key: str = Query(...)):
    if key != os.getenv("ADMIN_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden")
    Base.metadata.create_all(bind=engine)
    insp = inspect(engine)
    tables = sorted(insp.get_table_names())
    return {"ok": True, "tables": tables}

@router.post("/admin/migrate")
def migrate(key: str = Query(...)):
    if key != os.getenv("ADMIN_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden")

    stmts = [
        # limpia restos antiguos que provocan IntegrityError oculto como 409
        "ALTER TABLE apartments DROP COLUMN IF EXISTS telegram_chat_id",
        # permite name NULL
        "ALTER TABLE apartments ALTER COLUMN name DROP NOT NULL",
        # refuerza unicidad de code
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_apartments_code ON apartments (code)",
    ]

    executed, errors = [], []
    with engine.begin() as conn:
        for s in stmts:
            try:
                conn.execute(text(s))
                executed.append(s)
            except Exception as e:
                errors.append(f"{s} -- {e}")

    insp = inspect(engine)
    columns = {
        c["name"]: {"nullable": c.get("nullable", True), "type": str(c.get("type"))}
        for c in insp.get_columns("apartments")
    }

    return {"ok": True, "executed": executed, "errors": errors, "columns": columns}

