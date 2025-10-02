from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import inspect, text
from ..db import Base, engine
import os

router = APIRouter(prefix="/admin", tags=["admin"])

def _check(key: str | None = Query(default=None)):
    admin = os.getenv("ADMIN_KEY", "")
    if not admin or key != admin:
        raise HTTPException(status_code=403, detail="Forbidden")

@router.post("/init")
def init(key: str | None = Query(default=None)):
    _check(key)
    # crea tablas que falten
    Base.metadata.create_all(bind=engine)
    return db_ping(key)

@router.get("/db-ping")
def db_ping(key: str | None = Query(default=None)):
    _check(key)
    insp = inspect(engine)
    return {
        "ok": True,
        "tables": sorted(insp.get_table_names())
    }

def _migrate_apartments_and_expenses():
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    stmts: list[str] = []

    # apartments
    if "apartments" in tables:
        cols = {c["name"] for c in insp.get_columns("apartments")}
        if "is_active" not in cols:
            stmts.append("ALTER TABLE apartments ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true")
        if "created_at" not in cols:
            stmts.append("ALTER TABLE apartments ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now()")

    # expenses
    if "expenses" in tables:
        ecols = {c["name"] for c in insp.get_columns("expenses")}
        if "created_at" not in ecols:
            stmts.append("ALTER TABLE expenses ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now()")
        if "updated_at" not in ecols:
            stmts.append("ALTER TABLE expenses ADD COLUMN IF NOT EXISTS updated_at timestamptz")
        # si existiera amount_gross (antiguo), renómbralo a amount
        if "amount" not in ecols and "amount_gross" in ecols:
            stmts.append("ALTER TABLE expenses RENAME COLUMN amount_gross TO amount")

    executed = []
    if stmts:
        with engine.begin() as conn:
            for s in stmts:
                conn.execute(text(s))
                executed.append(s)
    return executed

@router.post("/migrate")
def migrate(key: str | None = Query(default=None)):
    _check(key)
    Base.metadata.create_all(bind=engine)  # por si la tabla no existía
    executed = _migrate_apartments_and_expenses()
    return {"ok": True, "executed": executed}