# app/routers/admin.py
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import text, inspect
from ..db import engine, Base
import os

router = APIRouter(prefix="/admin", tags=["admin"])

def _auth(
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
    key: str | None = Query(default=None),
):
    admin = os.getenv("ADMIN_KEY", "")
    provided = x_internal_key or key
    if not admin or provided != admin:
        raise HTTPException(status_code=403, detail="forbidden")

@router.get("/db-ping")
def db_ping(
    auth: None = Depends(_auth),
):
    with engine.connect() as conn:
        conn.execute(text("select 1"))
    insp = inspect(engine)
    return {"ok": True, "tables": insp.get_table_names()}

@router.post("/init")
def init_db(
    auth: None = Depends(_auth),
):
    # crea cualquier tabla que falte
    Base.metadata.create_all(bind=engine)
    insp = inspect(engine)
    return {"ok": True, "tables": insp.get_table_names()}