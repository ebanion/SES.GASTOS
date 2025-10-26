# app/db_simple.py - Configuración simplificada de base de datos
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Obtener DATABASE_URL de múltiples fuentes
DATABASE_URL = (
    os.getenv("DATABASE_URL") or 
    os.getenv("DATABASE_PRIVATE_URL") or 
    os.getenv("POSTGRES_URL") or 
    "sqlite:///local.db"
)

print(f"[DB] Using DATABASE_URL: {DATABASE_URL[:50]}...")

# Normalizar URL de PostgreSQL si es necesario
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "psycopg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# Crear engine con configuración optimizada
if "postgresql" in DATABASE_URL:
    print("[DB] 🐘 Configurando PostgreSQL...")
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_timeout=30,
        pool_recycle=3600,
        connect_args={
            "connect_timeout": 30,
            "application_name": "ses-gastos"
        }
    )
else:
    print("[DB] 📁 Configurando SQLite...")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Crear sesión y base
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency para obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Probar conexión a la base de datos"""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            if result == 1:
                print("[DB] ✅ Conexión exitosa")
                return True
    except Exception as e:
        print(f"[DB] ❌ Error de conexión: {e}")
        return False
    return False

def create_tables():
    """Crear todas las tablas"""
    try:
        from . import models  # Importar modelos
        Base.metadata.create_all(bind=engine)
        print("[DB] ✅ Tablas creadas")
        return True
    except Exception as e:
        print(f"[DB] ❌ Error creando tablas: {e}")
        return False