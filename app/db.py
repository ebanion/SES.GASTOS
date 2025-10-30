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
DATABASE_URL_RAW = os.getenv("DATABASE_URL")

# 🔧 CRÍTICO: Strip whitespace (espacios, \n, \r, \t)
if DATABASE_URL_RAW:
    DATABASE_URL = DATABASE_URL_RAW.strip()
    
    # Debug: Detectar whitespace
    if DATABASE_URL != DATABASE_URL_RAW:
        print(f"[DB] ⚠️ ADVERTENCIA: DATABASE_URL contenía whitespace")
        print(f"[DB]    Original length: {len(DATABASE_URL_RAW)}")
        print(f"[DB]    Stripped length: {len(DATABASE_URL)}")
        print(f"[DB]    Repr (últimos 30 chars): {repr(DATABASE_URL_RAW[-30:])}")
else:
    DATABASE_URL = None

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
        
        # 🔧 CRÍTICO: Convertir host externo a interno SOLO para Render PostgreSQL
        # ⚠️ NO APLICAR a otros proveedores (Aiven, Railway, etc.)
        is_render_postgres = (
            url.host and 
            ".render.com" in url.host and 
            url.host.startswith("dpg-") and
            ".postgres.render.com" in url.host
        )
        
        if is_render_postgres:
            internal_host = url.host.split(".")[0]  # Extraer solo dpg-xxxxx-a
            print(f"[DB] 🔄 Convirtiendo host externo a interno (Render PostgreSQL):")
            print(f"[DB]    Externo: {url.host}")
            print(f"[DB]    Interno: {internal_host}")
            url = url.set(host=internal_host)
        elif ".render.com" in url.host:
            print(f"[DB] ℹ️ Host Render detectado pero no es PostgreSQL managed: {url.host}")
        elif ".aivencloud.com" in url.host or ".railway.app" in url.host:
            print(f"[DB] ℹ️ Proveedor externo detectado: {url.host} (sin modificaciones)")
        
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
    
    # 🔍 Debug adicional (solo si DEBUG=1)
    if os.getenv("DEBUG") == "1":
        try:
            # Extraer password para verificar longitud
            import re as debug_re
            pass_match = debug_re.search(r'://[^:]+:([^@]+)@', DATABASE_URL)
            if pass_match:
                password_length = len(pass_match.group(1))
                print(f"[DB] 🔍 DEBUG: Password length = {password_length} chars")
                print(f"[DB] 🔍 DEBUG: URL total length = {len(DATABASE_URL)} chars")
                print(f"[DB] 🔍 DEBUG: URL repr (primeros 60): {repr(DATABASE_URL[:60])}")
        except Exception as debug_err:
            print(f"[DB] 🔍 DEBUG: Error en debug logging: {debug_err}")
    
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
        
        # 🔧 CRÍTICO: Solo fallback si NO es error de autenticación
        error_msg = str(pg_error).lower()
        is_auth_error = "authentication failed" in error_msg or "password" in error_msg
        
        if is_auth_error:
            print(f"[DB] 🚨 ERROR DE AUTENTICACIÓN - NO HAY FALLBACK")
            print(f"[DB]")
            print(f"[DB] 💡 Posibles causas:")
            print(f"[DB]    1. DATABASE_URL contiene whitespace (\\n, \\r, espacios)")
            print(f"[DB]    2. Password incorrecta o mal copiada")
            print(f"[DB]    3. Firewall bloqueando conexión (Aiven/Render)")
            print(f"[DB]")
            print(f"[DB] 🔧 Soluciones:")
            print(f"[DB]    1. Ejecuta: python diagnose_aiven.py (en Render Shell)")
            print(f"[DB]    2. Añade DEBUG=1 en Render Environment para ver password length")
            print(f"[DB]    3. Verifica firewall en Aiven Dashboard → Networking")
            print(f"[DB]    4. Usa el botón 'Copy' en Aiven para copiar la URL exacta")
            
            raise RuntimeError(f"PostgreSQL authentication failed: {pg_error}")
        
        # Fallback solo para otros errores (timeout, network, etc.)
        print(f"[DB] ⚠️ USANDO SQLITE COMO FALLBACK TEMPORAL (error no crítico)")
        print(f"[DB] 📁 Archivo: /opt/render/project/src/ses_gastos_persistent.db")
        
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
