# app/routers/admin.py
from __future__ import annotations

import os
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect

from ..db import engine, get_db, Base
from .. import models  # importa modelos para que SQLAlchemy conozca las tablas

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

    # 1) Garantiza columna buena
    stmts = [
        "ALTER TABLE apartments ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true",
        "ALTER TABLE apartments ALTER COLUMN name DROP NOT NULL",
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_apartments_code ON apartments (code)",
        "ALTER TABLE apartments DROP COLUMN IF EXISTS telegram_chat_id"
    ]

    executed, errors = [], []
    with engine.begin() as conn:
        # Ejecuta las simples
        for s in stmts:
            try:
                conn.execute(text(s))
                executed.append(s)
            except Exception as e:
                errors.append(f"{s} -- {e}")

        # 2) Si existe 'active', copia valores a is_active y elimina 'active'
        try:
            conn.execute(text("""
            DO $$
            BEGIN
              IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'apartments' AND column_name = 'active'
              ) THEN
                -- Copia valores
                UPDATE apartments
                SET is_active = COALESCE(is_active, active);

                -- Quita NOT NULL por si acaso y pon default
                EXECUTE 'ALTER TABLE apartments ALTER COLUMN active DROP NOT NULL';
                EXECUTE 'ALTER TABLE apartments ALTER COLUMN active SET DEFAULT TRUE';

                -- Elimina columna antigua
                ALTER TABLE apartments DROP COLUMN IF EXISTS active;
              END IF;
            END $$;
            """))
            executed.append("copy active -> is_active & drop active")
        except Exception as e:
            errors.append(f"copy/drop active -- {e}")

    # Para inspección post-migración
    insp = inspect(engine)
    columns = {
        c["name"]: {"nullable": c.get("nullable", True), "type": str(c.get("type"))}
        for c in insp.get_columns("apartments")
    }

    return {"ok": True, "executed": executed, "errors": errors, "columns": columns}


