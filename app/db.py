# app/db.py
from __future__ import annotations
import os
import re
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import make_url

# ------------------------------------------------------------
# Configuración de PostgreSQL con fallback temporal a SQLite
# ------------------------------------------------------------
print("[DB] 🐘 Iniciando configuración de base de datos PostgreSQL...")

# Obtener DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Verificar que DATABASE_URL esté configurada
if not DATABASE_URL:
    print("[DB] ⚠️ DATABASE_URL no está configurada")
    print("[DB] 📁 Usando SQLite como fallback temporal")
    DATABASE_URL = "sqlite:///ses_gastos_persistent.db"

# Si es PostgreSQL, intentar conectar
if DATABASE_URL and ("postgresql" in DATABASE_URL or "postgres" in DATABASE_URL):
    print(f"[DB] ✅ DATABASE_URL de PostgreSQL encontrada")
    
    # Normalizar URL para psycopg v3
    original_url = DATABASE_URL
    try:
        url = make_url(DATABASE_URL)
        
        # Normalizar a postgresql+psycopg para usar psycopg v3
        if url.drivername in ["postgres", "postgresql"]:
            url = url.set(drivername="postgresql+psycopg")
        
        # 🔧 CRÍTICO: Convertir host externo a interno para Render
        # Render requiere usar el host interno cuando la app corre dentro de Render
        if url.host and ".render.com" in url.host:
            internal_host = url.host.split(".")[0]  # Extraer solo dpg-xxxxx-a
            print(f"[DB] 🔄 Convirtiendo host externo a interno:")
            print(f"[DB]    Externo: {url.host}")
            print(f"[DB]    Interno: {internal_host}")
            url = url.set(host=internal_host)
        
        # Asegurar sslmode=require
        query_params = dict(url.query)
        if "sslmode" not in query_params:
            query_params["sslmode"] = "require"
            url = url.set(query=query_params)
        
        # Verificar puerto - solo asignar si es None
        # No sobrescribir puertos no estándar (ej: Aiven usa 12417)
        if url.port is None:
            url = url.set(port=5432)
            print(f"[DB] ℹ️ Puerto no especificado, usando :5432 por defecto")
            
        DATABASE_URL = str(url)
        
    except Exception as url_error:
        print(f"[DB] ⚠️ Error parseando URL: {url_error}")
        # Fallback manual
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
        elif DATABASE_URL.startswith("postgresql://"):
            DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
        
        # Convertir host externo a interno (método manual)
        if ".render.com" in DATABASE_URL:
            import re as regex
            match = regex.search(r'@([^:@]+\.render\.com)', DATABASE_URL)
            if match:
                external_host = match.group(1)
                internal_host = external_host.split(".")[0]
                DATABASE_URL = DATABASE_URL.replace(external_host, internal_host)
                print(f"[DB] 🔄 Host convertido: {external_host} → {internal_host}")
        
        if "sslmode=" not in DATABASE_URL:
            separator = "&" if "?" in DATABASE_URL else "?"
            DATABASE_URL += f"{separator}sslmode=require"
        
        # Solo añadir puerto si NO existe ningún puerto
        # No forzar 5432, respetar puerto existente (ej: Aiven usa 12417)
        if "@" in DATABASE_URL and not re.search(r'@[^/]+:\d+/', DATABASE_URL):
            # No hay puerto, añadir :5432 por defecto
            DATABASE_URL = re.sub(r'@([^/:]+)/', r'@\1:5432/', DATABASE_URL)
            print(f"[DB] ℹ️ Puerto no especificado, usando :5432 por defecto")
    
    # Logs (sin password)
    masked_url = re.sub(r"://([^:@]+):[^@]+@", r"://\1:***@", DATABASE_URL)
    print(f"[DB] 🔗 Conexión PostgreSQL: {masked_url}")
    
    try:
        url_check = make_url(DATABASE_URL)
        print(f"[DB] 🔌 Puerto: {url_check.port or 5432}")
        print(f"[DB] 🔒 SSL Mode: {url_check.query.get('sslmode', 'no configurado')}")
        print(f"[DB] 🗄️  Base de datos: {url_check.database}")
        print(f"[DB] 🌍 Host: {url_check.host}")
    except Exception as e:
        print(f"[DB] ⚠️ No se pudo verificar detalles de URL: {e}")
    
    # Versiones
    try:
        import sqlalchemy as _sa
        print(f"[DB] 📦 SQLAlchemy version: {_sa.__version__}")
    except Exception:
        pass
    
    try:
        import psycopg as _pg
        print(f"[DB] 📦 psycopg version: {_pg.__version__}")
    except Exception as e:
        print(f"[DB] ⚠️ psycopg no disponible: {e}")
    
    # Intentar conectar a PostgreSQL
    print("[DB] 🔧 Creando engine de PostgreSQL...")
    
    try:
        connect_args = {
            "connect_timeout": 10,
            "application_name": "ses-gastos"
        }
        
        pg_engine = create_engine(
            DATABASE_URL, 
            pool_pre_ping=True,
            connect_args=connect_args,
            pool_timeout=30,
            pool_recycle=1800,
            pool_size=5,
            max_overflow=10,
            echo=False
        )
        
        # Verificar conexión
        print("[DB] 🔍 Verificando conexión con PostgreSQL...")
        
        max_retries = 3
        connected = False
        
        for attempt in range(max_retries):
            try:
                with pg_engine.connect() as conn:
                    result = conn.execute(text("SELECT 1")).scalar()
                    if result != 1:
                        raise Exception("SELECT 1 no devolvió 1")
                    
                    db_version = conn.execute(text("SELECT version()")).scalar()
                    db_name = conn.execute(text("SELECT current_database()")).scalar()
                    
                    version_parts = db_version.split()
                    postgres_version = version_parts[1] if len(version_parts) > 1 else "desconocida"
                    
                    print(f"[DB] ✅ PostgreSQL CONECTADO exitosamente")
                    print(f"[DB] 🎯 Base de datos: {db_name}")
                    print(f"[DB] 📊 Versión PostgreSQL: {postgres_version}")
                    print(f"[DB] 🚀 Sistema listo para operar")
                    
                    engine = pg_engine
                    connected = True
                    break
                    
            except Exception as retry_error:
                print(f"[DB] ⚠️ Intento {attempt + 1}/{max_retries} falló: {retry_error}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2)
        
        if not connected:
            raise Exception("No se pudo conectar a PostgreSQL después de 3 intentos")
            
    except Exception as pg_error:
        print(f"[DB] ❌ PostgreSQL falló: {pg_error}")
        print(f"[DB] ⚠️ USANDO SQLITE COMO FALLBACK TEMPORAL")
        print(f"[DB] 📁 Archivo: /opt/render/project/src/ses_gastos_persistent.db")
        print(f"[DB]")
        print(f"[DB] 🔧 PARA ARREGLAR POSTGRESQL:")
        print(f"[DB]    1. Ve a Render Dashboard → Databases → dbname_datos")
        print(f"[DB]    2. Verifica que el estado sea 'Available'")
        print(f"[DB]    3. Copia la 'Internal Connection String' con el botón Copy")
        print(f"[DB]    4. Añade :5432 después del host")
        print(f"[DB]    5. Añade ?sslmode=require al final")
        print(f"[DB]    6. Actualiza DATABASE_URL en ses-gastos → Environment")
        
        DATABASE_URL = "sqlite:///ses_gastos_persistent.db"
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)

else:
    # SQLite directo
    print("[DB] 📁 Usando SQLite...")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Configuración de SessionLocal y Base
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency para obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Información final
db_type = "PostgreSQL" if "postgresql" in str(engine.url) else "SQLite"
print(f"[DB] 🎉 Configuración completada usando: {db_type}")

if "sqlite" in str(engine.url):
    print(f"[DB] ⚠️ TEMPORAL: Usando SQLite hasta que PostgreSQL funcione")
    print(f"[DB] 📌 Archivo: {engine.url}")
else:
    print(f"[DB] ✅ PostgreSQL configurado correctamente")
