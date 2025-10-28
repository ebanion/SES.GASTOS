# app/db.py
"""
Configuración de la base de datos PostgreSQL
IMPORTANTE: Este proyecto usa SOLO PostgreSQL en producción.
"""
from __future__ import annotations
import os
import re
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

# ------------------------------------------------------------
# Configuración de DATABASE_URL - Solo PostgreSQL
# ------------------------------------------------------------

# Intentar obtener DATABASE_URL de múltiples fuentes
DATABASE_URL = (
    os.getenv("DATABASE_URL") or 
    os.getenv("DATABASE_PRIVATE_URL") or 
    os.getenv("POSTGRES_URL")
)

if not DATABASE_URL:
    print("❌ [DB] ERROR: DATABASE_URL no está configurada")
    print("❌ [DB] Este proyecto requiere PostgreSQL.")
    print("💡 [DB] Configura una de estas variables de entorno:")
    print("   - DATABASE_URL")
    print("   - DATABASE_PRIVATE_URL")
    print("   - POSTGRES_URL")
    sys.exit(1)

# Determinar fuente de la variable
db_source = (
    'DATABASE_URL' if os.getenv('DATABASE_URL') else
    'DATABASE_PRIVATE_URL' if os.getenv('DATABASE_PRIVATE_URL') else  
    'POSTGRES_URL' if os.getenv('POSTGRES_URL') else 'NONE'
)
print(f"[DB] 📍 Usando DATABASE_URL desde: {db_source}")

# Normalizar URL de PostgreSQL para usar psycopg v3
if "postgresql" not in DATABASE_URL and "postgres" not in DATABASE_URL:
    print(f"❌ [DB] ERROR: La URL proporcionada no es de PostgreSQL")
    print(f"❌ [DB] URL recibida: {DATABASE_URL[:20]}...")
    sys.exit(1)

try:
    url = make_url(DATABASE_URL)
    # Normalizar a postgresql+psycopg (driver de psycopg v3)
    if url.drivername in ["postgres", "postgresql"]:
        url = url.set(drivername="postgresql+psycopg")
    elif url.drivername == "postgresql.psycopg":  # error común con '.'
        url = url.set(drivername="postgresql+psycopg")
    DATABASE_URL = str(url)
except Exception as url_error:
    print(f"[DB] ⚠️ URL parsing error, intentando corrección manual: {url_error}")
    # Fallback manual para normalizar la URL
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgresql.psycopg://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql.psycopg://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# Enmascarar contraseña para logs seguros
masked_url = re.sub(r"://([^:@]+):[^@]+@", r"://\1:***@", DATABASE_URL)
print(f"[DB] 🔗 Conexión: {masked_url}")

# Mostrar versiones de dependencias
try:
    import sqlalchemy as _sa
    print(f"[DB] 📦 SQLAlchemy: {_sa.__version__}")
except Exception:
    pass

try:
    import psycopg as _pg
    print(f"[DB] 📦 psycopg (v3): {_pg.__version__}")
except Exception as e:
    print(f"[DB] ❌ psycopg (v3) no disponible: {e}")
    print(f"[DB] 💡 Instala: pip install 'psycopg[binary]'")
    sys.exit(1)

# ------------------------------------------------------------
# Crear engine de PostgreSQL
# ------------------------------------------------------------

print("[DB] 🐘 Configurando PostgreSQL...")

# Configuración optimizada para PostgreSQL en producción
connect_args = {
    "connect_timeout": 10,
    "application_name": "ses-gastos-app"
}

try:
    engine = create_engine(
        DATABASE_URL, 
        pool_pre_ping=True,          # Verificar conexiones antes de usar
        connect_args=connect_args,
        pool_timeout=30,             # Timeout para obtener conexión del pool
        pool_recycle=1800,           # Reciclar conexiones cada 30 min
        pool_size=5,                 # Tamaño del pool de conexiones
        max_overflow=10,             # Conexiones adicionales permitidas
        echo=False                   # No mostrar SQL en logs (cambiar a True para debug)
    )
    
    print("[DB] 🔍 Verificando conexión a PostgreSQL...")
    
    # Test de conexión con reintentos
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                # Ejecutar SELECT 1 para verificar conexión
                result = conn.execute(text("SELECT 1")).scalar()
                if result != 1:
                    raise OperationalError("SELECT 1 falló", None, None)
                
                # Obtener versión de PostgreSQL
                version = conn.execute(text("SELECT version()")).scalar()
                pg_version = version.split()[1] if version else "desconocida"
                
                # Obtener nombre de la base de datos
                db_name = conn.execute(text("SELECT current_database()")).scalar()
                
                print(f"[DB] ✅ PostgreSQL CONECTADO exitosamente")
                print(f"[DB] 🎯 Base de datos: {db_name}")
                print(f"[DB] 📊 Versión PostgreSQL: {pg_version}")
                print(f"[DB] 🔌 Pool de conexiones: {engine.pool.size()} activas")
                break
                
        except OperationalError as retry_error:
            print(f"[DB] ⚠️ Intento {attempt + 1}/{max_retries} falló: {retry_error}")
            if attempt < max_retries - 1:
                import time
                print(f"[DB] ⏳ Reintentando en {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print(f"[DB] ❌ FALLO CRÍTICO: No se pudo conectar después de {max_retries} intentos")
                print(f"[DB] 🔍 URL: {masked_url}")
                print(f"[DB] 💡 Verifica:")
                print(f"   1. Las credenciales de PostgreSQL")
                print(f"   2. Que el servidor PostgreSQL esté corriendo")
                print(f"   3. Que el puerto 5432 esté accesible")
                print(f"   4. Que sslmode=require esté en la URL si es necesario")
                raise RuntimeError(f"No se pudo conectar a PostgreSQL: {retry_error}")
                
except Exception as critical_error:
    print(f"[DB] ❌ ERROR CRÍTICO al configurar PostgreSQL: {critical_error}")
    print(f"[DB] 🔍 Tipo de error: {type(critical_error).__name__}")
    print(f"[DB] 🐍 Python: {sys.version}")
    print(f"[DB] 💡 Este proyecto requiere PostgreSQL. No hay fallback a SQLite.")
    sys.exit(1)

# ------------------------------------------------------------
# Crear sesión y base declarativa
# ------------------------------------------------------------

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    Dependency para obtener sesión de base de datos.
    Se usa con FastAPI Depends.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

print("[DB] ✅ Módulo de base de datos inicializado correctamente")
