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
    print("[DB] 🐘 Configurando PostgreSQL...")
    try:
        # Configuración optimizada para Render PostgreSQL
        connect_args = {
            "connect_timeout": 30,
            "application_name": "ses-gastos-render",
            "sslmode": "require"
        }
        
        engine = create_engine(
            DATABASE_URL, 
            pool_pre_ping=True, 
            connect_args=connect_args,
            pool_timeout=60,
            pool_recycle=3600,
            echo=False
        )
        
        # Test de conexión inmediato con reintentos
        from sqlalchemy import text
        import time
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with engine.connect() as conn:
                    version = conn.execute(text("SELECT version()")).scalar()
                    print(f"[DB] ✅ PostgreSQL CONECTADO: {version.split()[1]}")
                    print(f"[DB] 🎯 Base de datos: dbname_zoe8")
                    break
            except Exception as retry_error:
                print(f"[DB] ⚠️ Intento {attempt + 1}/{max_retries} falló: {retry_error}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Esperar antes del siguiente intento
                else:
                    raise retry_error
            
    except Exception as pg_error:
        print(f"[DB] ❌ PostgreSQL falló después de {max_retries} intentos: {pg_error}")
        print(f"[DB] 🔍 URL problemática: {masked}")
        print(f"[DB] 🔍 Tipo de error: {type(pg_error).__name__}")
        
        # Información adicional para debugging
        import sys
        print(f"[DB] 🐍 Python version: {sys.version}")
        try:
            import psycopg
            print(f"[DB] 📦 psycopg version: {psycopg.__version__}")
        except ImportError as imp_err:
            print(f"[DB] ❌ psycopg import error: {imp_err}")
        
        # En producción, usar SQLite como fallback temporal
        print("[DB] ⚠️ PostgreSQL falló, usando SQLite como fallback temporal")
        print(f"[DB] 🔍 Error PostgreSQL: {pg_error}")
        db_dir = os.getenv("SQLITE_DIR", "/tmp")
        DATABASE_URL = f"sqlite:///{db_dir}/ses_gastos.db"
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        print(f"[DB] 📁 SQLite temporal: {db_dir}/ses_gastos.db")
        print("[DB] 💡 Esto permite que la app funcione mientras se arregla PostgreSQL")
        print("[DB] 🚨 IMPORTANTE: Los datos se perderán en cada despliegue hasta que PostgreSQL funcione")
else:
    print("[DB] 📁 Usando SQLite (desarrollo)...")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


