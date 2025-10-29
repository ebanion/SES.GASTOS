# app/db.py
from __future__ import annotations
import os
import re
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import make_url

# ------------------------------------------------------------
# Configuración exclusiva de PostgreSQL
# ------------------------------------------------------------
print("[DB] 🐘 Iniciando configuración de base de datos PostgreSQL...")

# ============================================================
# SOLO usar DATABASE_URL - sin fallbacks ni alternativas
# ============================================================
DATABASE_URL = os.getenv("DATABASE_URL")

# Verificar que DATABASE_URL esté configurada
if not DATABASE_URL:
    print("[DB] ❌ ERROR CRÍTICO: DATABASE_URL no está configurada")
    print("[DB] 💡 Configura la variable de entorno DATABASE_URL con:")
    print("[DB]    postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require")
    sys.exit(1)

# Verificar que sea PostgreSQL
if "postgresql" not in DATABASE_URL and "postgres" not in DATABASE_URL:
    print(f"[DB] ❌ ERROR CRÍTICO: DATABASE_URL no es PostgreSQL")
    print(f"[DB] 💡 La URL debe comenzar con 'postgresql://' o 'postgres://'")
    print(f"[DB] 💡 SQLite no está soportado en producción")
    sys.exit(1)

print(f"[DB] ✅ DATABASE_URL configurada correctamente")

# ------------------------------------------------------------
# Normalización de URL para usar psycopg (v3)
# ------------------------------------------------------------
try:
    url = make_url(DATABASE_URL)
    
    # Normalizar a postgresql+psycopg para usar psycopg v3
    if url.drivername in ["postgres", "postgresql"]:
        url = url.set(drivername="postgresql+psycopg")
    
    # Asegurar que tenga sslmode=require si no está presente
    query_params = dict(url.query)
    if "sslmode" not in query_params:
        query_params["sslmode"] = "require"
        url = url.set(query=query_params)
    
    # Verificar puerto (por defecto 5432 para PostgreSQL)
    if url.port is None:
        url = url.set(port=5432)
        
    DATABASE_URL = str(url)
    
except Exception as url_error:
    print(f"[DB] ⚠️ Error parseando URL: {url_error}")
    # Fallback manual para corrección de URL
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    
    # Asegurar sslmode=require
    if "sslmode=" not in DATABASE_URL:
        separator = "&" if "?" in DATABASE_URL else "?"
        DATABASE_URL += f"{separator}sslmode=require"
    
    # Asegurar puerto
    if ":5432/" not in DATABASE_URL and "@" in DATABASE_URL:
        # Insertar :5432 antes del /
        DATABASE_URL = re.sub(r'@([^/]+)/', r'@\1:5432/', DATABASE_URL)

# Logs útiles (sin password)
masked_url = re.sub(r"://([^:@]+):[^@]+@", r"://\1:***@", DATABASE_URL)
print(f"[DB] 🔗 Conexión PostgreSQL: {masked_url}")

# Verificar puerto en la URL
try:
    url_check = make_url(DATABASE_URL)
    print(f"[DB] 🔌 Puerto: {url_check.port or 5432}")
    print(f"[DB] 🔒 SSL Mode: {url_check.query.get('sslmode', 'no configurado')}")
    print(f"[DB] 🗄️  Base de datos: {url_check.database}")
    print(f"[DB] 🌍 Host: {url_check.host}")
except Exception as e:
    print(f"[DB] ⚠️ No se pudo verificar detalles de URL: {e}")

# Versiones de dependencias
try:
    import sqlalchemy as _sa
    print(f"[DB] 📦 SQLAlchemy version: {_sa.__version__}")
except Exception:
    pass

try:
    import psycopg as _pg
    print(f"[DB] 📦 psycopg version: {_pg.__version__}")
except Exception as e:
    print(f"[DB] ❌ psycopg no disponible: {e}")
    print(f"[DB] 💡 Instala psycopg con: pip install 'psycopg[binary]'")
    sys.exit(1)

# ------------------------------------------------------------
# Crear engine de PostgreSQL
# ------------------------------------------------------------
print("[DB] 🔧 Creando engine de PostgreSQL...")

try:
    # Configuración optimizada para PostgreSQL
    connect_args = {
        "connect_timeout": 10,
        "application_name": "ses-gastos"
    }
    
    engine = create_engine(
        DATABASE_URL, 
        pool_pre_ping=True,  # Verificar conexión antes de usar
        connect_args=connect_args,
        pool_timeout=30,
        pool_recycle=1800,  # Reciclar conexiones cada 30 minutos
        pool_size=5,  # Número de conexiones en el pool
        max_overflow=10,  # Conexiones adicionales permitidas
        echo=False  # No mostrar SQL queries en logs
    )
    
    # ------------------------------------------------------------
    # Verificación de conexión con SELECT 1
    # ------------------------------------------------------------
    print("[DB] 🔍 Verificando conexión con PostgreSQL...")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                # Test básico de conexión
                result = conn.execute(text("SELECT 1")).scalar()
                if result != 1:
                    raise Exception("SELECT 1 no devolvió 1")
                
                # Obtener información de la base de datos
                db_version = conn.execute(text("SELECT version()")).scalar()
                db_name = conn.execute(text("SELECT current_database()")).scalar()
                
                # Logs de éxito
                version_parts = db_version.split()
                postgres_version = version_parts[1] if len(version_parts) > 1 else "desconocida"
                
                print(f"[DB] ✅ PostgreSQL CONECTADO exitosamente")
                print(f"[DB] 🎯 Base de datos: {db_name}")
                print(f"[DB] 📊 Versión PostgreSQL: {postgres_version}")
                print(f"[DB] 🚀 Sistema listo para operar")
                break
                
        except Exception as retry_error:
            print(f"[DB] ⚠️ Intento {attempt + 1}/{max_retries} falló: {retry_error}")
            if attempt < max_retries - 1:
                import time
                time.sleep(2)  # Esperar antes del siguiente intento
            else:
                print(f"[DB] ❌ ERROR: No se pudo conectar a PostgreSQL después de {max_retries} intentos")
                print(f"[DB] 🔍 URL (enmascarada): {masked_url}")
                print(f"[DB] 💡 Verifica:")
                print(f"[DB]    1. Que la base de datos PostgreSQL esté en línea")
                print(f"[DB]    2. Que las credenciales sean correctas")
                print(f"[DB]    3. Que el firewall permita conexiones al puerto 5432")
                print(f"[DB]    4. Que sslmode=require esté configurado correctamente")
                print(f"[DB]    5. Que el dominio completo esté en la URL (ej: .frankfurt-postgres.render.com)")
                raise retry_error
        
except Exception as pg_error:
    print(f"[DB] ❌ ERROR CRÍTICO al configurar PostgreSQL: {pg_error}")
    print(f"[DB] 🔍 Tipo de error: {type(pg_error).__name__}")
    print(f"[DB] 🔍 Detalles: {str(pg_error)}")
    print(f"[DB] 💡 La aplicación no puede continuar sin PostgreSQL")
    print(f"[DB] 💡 SQLite no está disponible como fallback en producción")
    print(f"[DB]")
    print(f"[DB] 🔧 Solución:")
    print(f"[DB]    Configura DATABASE_URL en Render Environment con:")
    print(f"[DB]    postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require")
    print(f"[DB]")
    print(f"[DB]    Ejemplo correcto:")
    print(f"[DB]    postgresql://ses_gastos_user:PASSWORD@dpg-xxx.frankfurt-postgres.render.com:5432/ses_gastos?sslmode=require")
    sys.exit(1)

# ------------------------------------------------------------
# Configuración de SessionLocal y Base
# ------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency para obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------------------------------------------
# Información final
# ------------------------------------------------------------
print("[DB] 🎉 Configuración de base de datos completada")
print("[DB] 📌 Sistema configurado EXCLUSIVAMENTE con PostgreSQL")
print("[DB] 🚫 SQLite no está disponible ni como fallback")
print("[DB] ✅ Usando SOLO la variable DATABASE_URL")
