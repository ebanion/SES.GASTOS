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
# Intentar múltiples fuentes de DATABASE_URL
DATABASE_URL = (
    os.getenv("DATABASE_URL") or 
    os.getenv("DATABASE_PRIVATE_URL") or 
    os.getenv("POSTGRES_URL") or 
    "sqlite:///local.db"
)

print(f"[DB] Intentando con DATABASE_URL desde: {
    'DATABASE_URL' if os.getenv('DATABASE_URL') else
    'DATABASE_PRIVATE_URL' if os.getenv('DATABASE_PRIVATE_URL') else  
    'POSTGRES_URL' if os.getenv('POSTGRES_URL') else
    'fallback SQLite'
}")

# Normalizar URL de PostgreSQL
if DATABASE_URL and "postgresql" in DATABASE_URL:
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
    except Exception as url_error:
        print(f"[DB] URL parsing error: {url_error}")
        # Fallback manual
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

# Forzar uso de PostgreSQL si está disponible
if "postgresql" in DATABASE_URL:
    print("[DB] 🐘 Forzando PostgreSQL...")
    try:
        # Configuración optimizada para Render PostgreSQL
        connect_args = {
            "connect_timeout": 60,
            "application_name": "ses-gastos-render"
        }
        
        engine = create_engine(
            DATABASE_URL, 
            pool_pre_ping=True, 
            connect_args=connect_args,
            pool_timeout=60,
            pool_recycle=3600,
            echo=False
        )
        
        # Test de conexión inmediato
        from sqlalchemy import text
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version()")).scalar()
            print(f"[DB] ✅ PostgreSQL FUNCIONANDO: {version.split()[1]}")
            
    except Exception as pg_error:
        print(f"[DB] ❌ PostgreSQL falló: {pg_error}")
        print("[DB] 🔄 Usando SQLite como fallback...")
        db_dir = os.getenv("SQLITE_DIR", "/tmp")
        DATABASE_URL = f"sqlite:///{db_dir}/ses_gastos.db"
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        print(f"[DB] SQLite: {db_dir}/ses_gastos.db")
else:
    print("[DB] 📁 Usando SQLite...")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


