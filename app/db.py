# app/db.py - Configuración simplificada y robusta de base de datos
import os
import re
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Obtener DATABASE_URL de múltiples fuentes
DATABASE_URL = (
    os.getenv("DATABASE_URL") or 
    os.getenv("DATABASE_PRIVATE_URL") or 
    os.getenv("POSTGRES_URL") or 
    "sqlite:///local.db"
)

print(f"[DB] Fuente de DATABASE_URL: {
    'DATABASE_URL' if os.getenv('DATABASE_URL') else
    'DATABASE_PRIVATE_URL' if os.getenv('DATABASE_PRIVATE_URL') else  
    'POSTGRES_URL' if os.getenv('POSTGRES_URL') else
    'SQLite local'
}")

# Normalizar URL de PostgreSQL de forma simple y robusta
original_url = DATABASE_URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
    print("[DB] 🔧 Convertido postgres:// -> postgresql+psycopg://")
elif DATABASE_URL.startswith("postgresql://") and "psycopg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    print("[DB] 🔧 Convertido postgresql:// -> postgresql+psycopg://")

# Log de URL (enmascarando password)
masked_url = re.sub(r"://([^:@]+):[^@]+@", r"://\1:***@", DATABASE_URL)
print(f"[DB] URL final: {masked_url}")

# Mostrar versiones para debugging
try:
    import sqlalchemy as _sa
    print(f"[DB] SQLAlchemy: {_sa.__version__}")
except Exception:
    pass

try:
    import psycopg as _pg
    print(f"[DB] psycopg: {_pg.__version__}")
except Exception as e:
    print(f"[DB] psycopg no disponible: {e}")

# Crear engine con configuración optimizada
def create_database_engine():
    """Crear engine de base de datos con manejo de errores"""
    global DATABASE_URL
    
    if "postgresql" in DATABASE_URL:
        print("[DB] 🐘 Configurando PostgreSQL...")
        try:
            engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,
                pool_timeout=30,
                pool_recycle=3600,
                connect_args={
                    "connect_timeout": 30,
                    "application_name": "ses-gastos"
                },
                echo=False
            )
            
            # Test de conexión
            with engine.connect() as conn:
                version = conn.execute(text("SELECT version()")).scalar()
                print(f"[DB] ✅ PostgreSQL conectado: {version.split()[1]}")
                return engine
                
        except Exception as pg_error:
            print(f"[DB] ❌ PostgreSQL falló: {pg_error}")
            print("[DB] 🔄 Fallback a SQLite...")
            
            # Fallback a SQLite
            db_dir = os.getenv("SQLITE_DIR", "/tmp")
            DATABASE_URL = f"sqlite:///{db_dir}/ses_gastos.db"
            
    # SQLite (original o fallback)
    print(f"[DB] 📁 Usando SQLite: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    # Test de conexión SQLite
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[DB] ✅ SQLite conectado")
    except Exception as e:
        print(f"[DB] ❌ Error SQLite: {e}")
        raise
    
    return engine

# Crear engine
engine = create_database_engine()
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
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"[DB] Error de conexión: {e}")
        return False

def create_tables():
    """Crear todas las tablas"""
    try:
        from . import models  # Importar modelos
        Base.metadata.create_all(bind=engine)
        print("[DB] ✅ Tablas creadas/actualizadas")
        return True
    except Exception as e:
        print(f"[DB] ❌ Error creando tablas: {e}")
        return False


