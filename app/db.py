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
    # Configuración específica para PostgreSQL en Render
    if "postgresql" in DATABASE_URL:
        # Configuración optimizada para Render
        connect_args = {
            "connect_timeout": 30,
            "application_name": "ses-gastos"
        }
        engine = create_engine(
            DATABASE_URL, 
            pool_pre_ping=True, 
            connect_args=connect_args,
            pool_timeout=30,
            pool_recycle=3600
        )
    else:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
    
    # Test connection con más detalles
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        if "postgresql" in DATABASE_URL:
            version = conn.execute(text("SELECT version()")).scalar()
            print(f"[DB] ✅ PostgreSQL connection successful: {version[:50]}...")
        else:
            print("[DB] ✅ Database connection successful")
            
except Exception as e:
    print(f"[DB] ❌ Database connection failed: {type(e).__name__}: {e}")
    
    # Información adicional para debugging
    if "postgresql" in DATABASE_URL:
        print(f"[DB] 🔍 PostgreSQL connection details:")
        print(f"[DB]   - URL pattern: postgresql+psycopg://user:***@host:port/db")
        print(f"[DB]   - Error type: {type(e).__name__}")
        
        # Intentar con diferentes drivers si es problema de psycopg
        if "psycopg" in str(e).lower() or "driver" in str(e).lower():
            print(f"[DB] 🔄 Trying alternative PostgreSQL driver...")
            try:
                alt_url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
                alt_engine = create_engine(alt_url, pool_pre_ping=True)
                with alt_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                engine = alt_engine
                DATABASE_URL = alt_url
                print("[DB] ✅ Alternative PostgreSQL driver successful")
            except Exception as alt_e:
                print(f"[DB] ❌ Alternative driver also failed: {alt_e}")
                raise e
        else:
            raise e
    else:
        raise e
        
except Exception as final_e:
    print(f"[DB] 🔄 Falling back to SQLite for development")
    # Fallback to SQLite if PostgreSQL fails
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


