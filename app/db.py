# app/db.py
from __future__ import annotations
import os
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import make_url

# ------------------------------------------------------------
# Normalización de DATABASE_URL -> postgresql+psycopg
# ------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db")

try:
    url = make_url(DATABASE_URL)

    # Corrige variantes comunes
    if url.drivername == "postgres":
        url = url.set(drivername="postgresql+psycopg")
    elif url.drivername == "postgresql":
        url = url.set(drivername="postgresql+psycopg")
    elif url.drivername == "postgresql.psycopg":  # error típico con '.'
        url = url.set(drivername="postgresql+psycopg")

    DATABASE_URL = str(url)
except Exception:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgresql.psycopg://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql.psycopg://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# Logs útiles (sin password)
masked = re.sub(r"://([^:@]+):[^@]+@", r"://\1:***@", DATABASE_URL)
print(f"[DB] Using DATABASE_URL = {masked}")

# Versiones (para verificar en Render qué instaló realmente)
try:
    import sqlalchemy as _sa
    print(f"[DB] SQLAlchemy version: {_sa.__version__}")
except Exception as _:
    pass

try:
    import psycopg as _pg
    print(f"[DB] psycopg (v3) version: {_pg.__version__}")
except Exception as e:
    print(f"[DB] psycopg (v3) not importable: {e}")

# ------------------------------------------------------------
# Crear engine (solo psycopg v3)
# ------------------------------------------------------------
connect_args = {}

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
    # Test connection
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("[DB] ✅ Database connection successful")
except Exception as e:
    print(f"[DB] ❌ Database connection failed: {e}")
    print(f"[DB] 🔄 Falling back to SQLite for development")
    # Fallback to SQLite if PostgreSQL fails
    # Usar directorio persistente si está disponible
    import tempfile
    db_dir = os.getenv("SQLITE_DIR", "/tmp")
    DATABASE_URL = f"sqlite:///{db_dir}/ses_gastos.db"
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    print(f"[DB] SQLite path: {db_dir}/ses_gastos.db")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


