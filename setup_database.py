#!/usr/bin/env python3
"""
Script para configurar y verificar la base de datos
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

def test_database_connection():
    """Probar conexión a la base de datos PostgreSQL"""
    database_url = (
        os.getenv("DATABASE_URL") or 
        os.getenv("DATABASE_PRIVATE_URL") or 
        os.getenv("POSTGRES_URL")
    )
    
    if not database_url:
        print("❌ DATABASE_URL no está configurada")
        print("💡 Configura una de estas variables:")
        print("   - DATABASE_URL")
        print("   - DATABASE_PRIVATE_URL")
        print("   - POSTGRES_URL")
        return False
    
    # Verificar que sea PostgreSQL
    if "postgresql" not in database_url and "postgres" not in database_url:
        print("❌ DATABASE_URL no es PostgreSQL")
        print(f"💡 La URL debe comenzar con 'postgresql://' o 'postgres://'")
        return False
    
    # Normalizar URL para psycopg
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    
    # Enmascarar password para logs
    import re
    masked_url = re.sub(r"://([^:@]+):[^@]+@", r"://\1:***@", database_url)
    print(f"🔍 Probando conexión a PostgreSQL: {masked_url}")
    
    try:
        engine = create_engine(
            database_url, 
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": 10,
                "application_name": "ses-gastos-setup"
            }
        )
        
        with engine.connect() as conn:
            # Verificación básica
            result = conn.execute(text("SELECT 1")).scalar()
            if result != 1:
                raise Exception("SELECT 1 no devolvió 1")
            
            # Información de la base de datos
            version = conn.execute(text("SELECT version()")).scalar()
            db_name = conn.execute(text("SELECT current_database()")).scalar()
            
            print(f"✅ Conexión a PostgreSQL exitosa")
            print(f"🎯 Base de datos: {db_name}")
            print(f"📊 Versión: {version.split()[1] if version else 'desconocida'}")
            return True
            
    except OperationalError as e:
        print(f"❌ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def create_tables():
    """Crear tablas si no existen"""
    try:
        from app.db import engine, Base
        from app import models  # Importar modelos para crear tablas
        
        print("🔧 Creando tablas...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Configurando base de datos PostgreSQL para SES.GASTOS")
    print("=" * 60)
    
    # Verificar variables de entorno
    env_vars = ["DATABASE_URL", "POSTGRES_URL", "DATABASE_PRIVATE_URL"]
    found_config = False
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Verificar si es PostgreSQL
            is_postgres = "postgresql" in value or "postgres" in value
            status = "✅ PostgreSQL" if is_postgres else "⚠️ No es PostgreSQL"
            masked = "***" + value[-10:] if len(value) > 10 else "***"
            print(f"🔑 {var}: {masked} ({status})")
            if is_postgres:
                found_config = True
        else:
            print(f"❌ {var}: NO CONFIGURADA")
    
    print("=" * 60)
    
    if not found_config:
        print("❌ No se encontró ninguna configuración de PostgreSQL")
        print("💡 Configura DATABASE_URL con tu conexión PostgreSQL")
        return 1
    
    # Probar conexión
    if test_database_connection():
        print("🎯 Base de datos PostgreSQL conectada correctamente")
        
        # Crear tablas
        if create_tables():
            print("")
            print("=" * 60)
            print("🎉 Base de datos configurada exitosamente")
            print("✅ Sistema listo para usar con PostgreSQL")
            print("🚫 SQLite no está disponible (solo PostgreSQL en producción)")
            print("=" * 60)
            return 0
        else:
            print("❌ Error configurando tablas")
            return 1
    else:
        print("")
        print("=" * 60)
        print("❌ No se pudo conectar a PostgreSQL")
        print("")
        print("💡 Soluciones:")
        print("   1. Verifica que DATABASE_URL esté configurada en las variables de entorno")
        print("   2. Verifica que la base de datos PostgreSQL esté en línea")
        print("   3. Verifica las credenciales (usuario, password, host, puerto)")
        print("   4. Verifica que sslmode=require esté en la URL")
        print("   5. Verifica que el puerto sea 5432")
        print("")
        print("⚠️  SQLite no está soportado - solo PostgreSQL")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())