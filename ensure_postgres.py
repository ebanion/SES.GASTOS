#!/usr/bin/env python3
"""
Script para asegurar que PostgreSQL esté configurado correctamente
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

def ensure_postgres_connection():
    """Asegurar que PostgreSQL esté funcionando correctamente"""
    
    # Obtener DATABASE_URL
    database_url = (
        os.getenv("DATABASE_URL") or 
        os.getenv("DATABASE_PRIVATE_URL") or 
        os.getenv("POSTGRES_URL")
    )
    
    if not database_url:
        print("❌ No se encontró DATABASE_URL")
        return False
    
    if "postgresql" not in database_url:
        print(f"❌ DATABASE_URL no es PostgreSQL: {database_url}")
        return False
    
    # Normalizar URL
    try:
        url = make_url(database_url)
        if url.drivername == "postgres":
            url = url.set(drivername="postgresql+psycopg")
        elif url.drivername == "postgresql":
            url = url.set(drivername="postgresql+psycopg")
        database_url = str(url)
    except Exception as e:
        print(f"⚠️ Error normalizando URL: {e}")
        # Fallback manual
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    
    # Probar conexión
    try:
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": 30,
                "application_name": "ses-gastos-setup"
            }
        )
        
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version()")).scalar()
            db_name = conn.execute(text("SELECT current_database()")).scalar()
            
        print(f"✅ PostgreSQL conectado exitosamente")
        print(f"🎯 Base de datos: {db_name}")
        print(f"📊 Versión: {version.split()[1]}")
        
        # Verificar tablas
        with engine.connect() as conn:
            tables_check = {}
            for table in ["apartments", "expenses", "incomes", "reservations", "users"]:
                try:
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    tables_check[table] = count
                    print(f"📋 Tabla {table}: {count} registros")
                except Exception as e:
                    tables_check[table] = f"Error: {e}"
                    print(f"❌ Tabla {table}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a PostgreSQL: {e}")
        return False

def create_tables_if_needed():
    """Crear tablas si no existen"""
    try:
        # Importar después de verificar conexión
        from app.db import engine, Base
        from app import models  # Importar modelos
        
        print("🔧 Creando tablas si no existen...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas/verificadas")
        
        return True
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Verificando configuración de PostgreSQL...")
    print("=" * 50)
    
    # 1. Verificar conexión
    if not ensure_postgres_connection():
        print("\n❌ FALLO: No se pudo conectar a PostgreSQL")
        sys.exit(1)
    
    # 2. Crear tablas
    if not create_tables_if_needed():
        print("\n❌ FALLO: No se pudieron crear las tablas")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ PostgreSQL configurado correctamente")
    print("🎯 Base de datos: dbname_zoe8")
    print("🚀 Sistema listo para usar")

if __name__ == "__main__":
    main()