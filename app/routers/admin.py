# app/routers/admin.py
from __future__ import annotations
import os
from fastapi import APIRouter, HTTPException, Header, Query
from sqlalchemy import text, inspect
from ..db import engine

router = APIRouter(prefix="/admin", tags=["admin"])

def _require_admin(
    key: str | None = Query(default=None),
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
):
    admin = os.getenv("ADMIN_KEY") or ""
    provided = key or x_internal_key or ""
    if not admin or provided != admin:
        raise HTTPException(status_code=403, detail="Forbidden")

@router.get("/health")
def health():
    return {"ok": True}

@router.get("/db-ping")
def db_ping(
    key: str | None = None,
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
):
    _require_admin(key, x_internal_key)
    insp = inspect(engine)
    return {"ok": True, "tables": sorted(insp.get_table_names())}

@router.post("/init")
def init(
    key: str | None = None,
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
):
    _require_admin(key, x_internal_key)
    from ..db import Base
    from .. import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    insp = inspect(engine)
    return {"ok": True, "tables": sorted(insp.get_table_names())}

@router.get("/describe/{table}")
def describe(
    table: str,
    key: str | None = None,
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
):
    _require_admin(key, x_internal_key)
    sql = """
    SELECT column_name AS name, is_nullable, data_type
    FROM information_schema.columns
    WHERE table_name = :t
    ORDER BY ordinal_position
    """
    with engine.begin() as conn:
        rows = conn.execute(text(sql), {"t": table}).mappings().all()
    return {
        "ok": True,
        "table": table,
        "columns": {
            r["name"]: {"nullable": (r["is_nullable"] == "YES"), "type": r["data_type"]}
            for r in rows
        },
    }

@router.post("/migrate")
def migrate(
    key: str | None = None,
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
):
    _require_admin(key, x_internal_key)

    executed: list[str] = []
    errors: list[str] = []

    def try_exec(conn, sql: str):
        try:
            conn.execute(text(sql))
            executed.append(sql)
        except Exception as e:
            errors.append(f"{sql} -- {e}")

    def col_exists(conn, table: str, col: str) -> bool:
        q = """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = :t AND column_name = :c
        """
        r = conn.execute(text(q), {"t": table, "c": col}).first()
        return bool(r)

    with engine.begin() as conn:
        # ---------- APARTMENTS ----------
        try_exec(conn, "ALTER TABLE apartments ALTER COLUMN id TYPE varchar(36) USING id::text")
        try_exec(conn, "CREATE UNIQUE INDEX IF NOT EXISTS ux_apartments_code ON apartments (code)")
        try_exec(conn, "ALTER TABLE apartments ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true")
        try_exec(conn, "ALTER TABLE apartments ALTER COLUMN name DROP NOT NULL")
        try_exec(conn, "ALTER TABLE apartments DROP COLUMN IF EXISTS telegram_chat_id")

        # ---------- EXPENSES ----------
        try_exec(conn, "ALTER TABLE expenses ALTER COLUMN id TYPE varchar(36) USING id::text")
        try_exec(conn, "ALTER TABLE expenses ALTER COLUMN apartment_id TYPE varchar(36) USING apartment_id::text")

        # amount -> amount_gross si procede
        has_amount = col_exists(conn, "expenses", "amount")
        has_amount_gross = col_exists(conn, "expenses", "amount_gross")
        if has_amount and not has_amount_gross:
            try_exec(conn, "ALTER TABLE expenses RENAME COLUMN amount TO amount_gross")
            has_amount_gross = True
        if not has_amount_gross:
            try_exec(conn, "ALTER TABLE expenses ADD COLUMN amount_gross numeric(12,2)")

        # columnas opcionales
        try_exec(conn, "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS currency varchar(3)")
        try_exec(conn, "ALTER TABLE expenses ALTER COLUMN currency SET DEFAULT 'EUR'")
        try_exec(conn, "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS category varchar(50)")
        try_exec(conn, "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS description varchar(500)")
        try_exec(conn, "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS vendor varchar(255)")
        try_exec(conn, "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS invoice_number varchar(128)")
        try_exec(conn, "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS source varchar(50)")
        try_exec(conn, "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS vat_rate integer")
        try_exec(conn, "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS file_url text")
        try_exec(conn, "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS status varchar(20)")
        try_exec(conn, "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS created_at timestamp with time zone")

        # FK limpia
        try_exec(conn, "ALTER TABLE expenses DROP CONSTRAINT IF EXISTS expenses_apartment_id_fkey")
        try_exec(conn, "ALTER TABLE expenses ADD CONSTRAINT expenses_apartment_id_fkey FOREIGN KEY (apartment_id) REFERENCES apartments(id) ON DELETE CASCADE")

        # ---------- RESERVATIONS ----------
        try_exec(conn, "ALTER TABLE reservations ALTER COLUMN id TYPE varchar(36) USING id::text")
        try_exec(conn, "ALTER TABLE reservations ADD COLUMN IF NOT EXISTS apartment_id varchar(36)")
        try_exec(conn, "ALTER TABLE reservations DROP CONSTRAINT IF EXISTS reservations_apartment_id_fkey")
        try_exec(conn, "ALTER TABLE reservations ADD CONSTRAINT reservations_apartment_id_fkey FOREIGN KEY (apartment_id) REFERENCES apartments(id) ON DELETE SET NULL")

    with engine.begin() as conn:
        cols_exp = conn.execute(
            text("""
                SELECT column_name, is_nullable, data_type
                FROM information_schema.columns
                WHERE table_name='expenses'
                ORDER BY ordinal_position
            """)
        ).mappings().all()

        cols_res = conn.execute(
            text("""
                SELECT column_name, is_nullable, data_type
                FROM information_schema.columns
                WHERE table_name='reservations'
                ORDER BY ordinal_position
            """)
        ).mappings().all()

    return {
        "ok": True,
        "executed": executed,
        "errors": errors,
        "expenses_columns": {
            r["column_name"]: {"nullable": (r["is_nullable"] == "YES"), "type": r["data_type"]}
            for r in cols_exp
        },
        "reservations_columns": {
            r["column_name"]: {"nullable": (r["is_nullable"] == "YES"), "type": r["data_type"]}
            for r in cols_res
        },
    }

# ---------- SQL arbitrario seguro ----------
# ---------- SQL arbitrario seguro ----------
from fastapi import Body, Request

@router.post("/sql")
async def exec_sql(
    request: Request,
    key: str | None = Query(default=None),
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
    body_text: str | None = Body(default=None, media_type="text/plain"),
):
    """
    Ejecuta SQL arbitrario (solo ADMIN_KEY).

    Acepta:
      - text/plain -> el SQL directo en el cuerpo
      - application/json -> {"sql": "sentencias; separadas; por; ;"}

    Si envías JSON con ConvertTo-Json en PowerShell, aquí lo parseamos.
    """
    _require_admin(key, x_internal_key)

    raw = None

    # 1) Si viene como JSON, intenta extraer el campo "sql"
    try:
        if "application/json" in (request.headers.get("content-type") or "").lower():
            data = await request.json()
            if isinstance(data, dict) and isinstance(data.get("sql"), str):
                raw = data["sql"]
    except Exception:
        pass

    # 2) Si no, usa texto plano si llegó algo
    if raw is None and body_text:
        raw = body_text

    # 3) Último recurso: leer cuerpo bruto
    if raw is None:
        raw_bytes = await request.body()
        raw = raw_bytes.decode("utf-8", errors="ignore")

    raw = (raw or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty SQL")

    # Separar por ';'
    stmts = [s.strip() for s in raw.split(";") if s.strip()]
    executed, errors = [], []

    from sqlalchemy import text as sql_text
    with engine.begin() as conn:
        for s in stmts:
            try:
                conn.execute(sql_text(s))
                executed.append(s)
            except Exception as e:
                errors.append(f"{s} -- {e}")

    return {"ok": True, "executed": executed, "errors": errors}
