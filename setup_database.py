#!/usr/bin/env python3
"""
Script para configurar y verificar la base de datos
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

def test_database_connection():
    """Probar conexión a la base de datos"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL no está configurada")
        return False
    
    # Enmascarar password para logs
    import re
    masked_url = re.sub(r"://([^:@]+):[^@]+@", r"://\1:***@", database_url)
    print(f"🔍 Probando conexión a: {masked_url}")
    
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            if result == 1:
                print("✅ Conexión a PostgreSQL exitosa")
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
    print("🚀 Configurando base de datos para SES.GASTOS")
    print("=" * 50)
    
    # Verificar variables de entorno
    env_vars = ["DATABASE_URL", "POSTGRES_URL", "DATABASE_PRIVATE_URL"]
    for var in env_vars:
        value = os.getenv(var)
        if value:
            masked = "***" + value[-10:] if len(value) > 10 else "***"
            print(f"🔑 {var}: {masked}")
        else:
            print(f"❌ {var}: NO CONFIGURADA")
    
    print("=" * 50)
    
    # Probar conexión
    if test_database_connection():
        print("🎯 Base de datos conectada correctamente")
        
        # Crear tablas
        if create_tables():
            print("🎉 Base de datos configurada exitosamente")
            return 0
        else:
            print("❌ Error configurando tablas")
            return 1
    else:
        print("❌ No se pudo conectar a la base de datos")
        print("💡 Soluciones:")
        print("   1. Configurar DATABASE_URL en Render")
        print("   2. Crear base de datos PostgreSQL en Render")
        print("   3. Verificar credenciales de la base de datos")
        return 1

if __name__ == "__main__":
    sys.exit(main())