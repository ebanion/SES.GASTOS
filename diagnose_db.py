#!/usr/bin/env python3
"""
Script de diagnóstico completo para la base de datos
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

def diagnose_database():
    """Diagnóstico completo de la base de datos"""
    print("🔍 DIAGNÓSTICO DE BASE DE DATOS - SES.GASTOS")
    print("=" * 60)
    
    # 1. Verificar variables de entorno
    print("\n1. VARIABLES DE ENTORNO:")
    env_vars = {
        "DATABASE_URL": os.getenv("DATABASE_URL"),
        "DATABASE_PRIVATE_URL": os.getenv("DATABASE_PRIVATE_URL"), 
        "POSTGRES_URL": os.getenv("POSTGRES_URL")
    }
    
    for var, value in env_vars.items():
        if value:
            # Enmascarar password
            import re
            masked = re.sub(r"://([^:@]+):[^@]+@", r"://\1:***@", value)
            print(f"   ✅ {var}: {masked}")
        else:
            print(f"   ❌ {var}: NO CONFIGURADA")
    
    # Determinar DATABASE_URL a usar
    database_url = env_vars["DATABASE_URL"] or env_vars["DATABASE_PRIVATE_URL"] or env_vars["POSTGRES_URL"]
    
    if not database_url:
        print("\n❌ CRÍTICO: Ninguna variable de base de datos configurada")
        return False
    
    # 2. Normalizar URL
    print(f"\n2. NORMALIZACIÓN DE URL:")
    original_url = database_url
    
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
        print("   🔧 Convertido postgres:// -> postgresql+psycopg://")
    elif database_url.startswith("postgresql://") and "psycopg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        print("   🔧 Convertido postgresql:// -> postgresql+psycopg://")
    
    print(f"   📝 URL final: {database_url[:50]}...")
    
    # 3. Probar conexión
    print(f"\n3. PRUEBA DE CONEXIÓN:")
    try:
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 30} if "postgresql" in database_url else {}
        )
        
        with engine.connect() as conn:
            if "postgresql" in database_url:
                version = conn.execute(text("SELECT version()")).scalar()
                print(f"   ✅ PostgreSQL conectado: {version.split()[1]}")
            else:
                conn.execute(text("SELECT 1"))
                print(f"   ✅ SQLite conectado")
            
            # 4. Verificar tablas existentes
            print(f"\n4. TABLAS EXISTENTES:")
            if "postgresql" in database_url:
                tables_query = """
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
                """
            else:
                tables_query = """
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name
                """
            
            result = conn.execute(text(tables_query))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                for table in tables:
                    # Contar registros
                    try:
                        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = count_result.scalar()
                        print(f"   ✅ {table}: {count} registros")
                    except Exception as e:
                        print(f"   ⚠️ {table}: Error contando - {e}")
            else:
                print("   ❌ No hay tablas creadas")
            
            # 5. Verificar modelos de SQLAlchemy
            print(f"\n5. VERIFICACIÓN DE MODELOS:")
            try:
                sys.path.append('.')
                from app.db import Base
                from app import models
                
                expected_tables = ["users", "apartments", "expenses", "incomes", "reservations", "idempotency_keys"]
                missing_tables = [t for t in expected_tables if t not in tables]
                
                if missing_tables:
                    print(f"   ⚠️ Tablas faltantes: {', '.join(missing_tables)}")
                    print("   💡 Ejecutar: Base.metadata.create_all(bind=engine)")
                else:
                    print("   ✅ Todas las tablas requeridas existen")
                    
            except ImportError as e:
                print(f"   ❌ Error importando modelos: {e}")
            
            return True
            
    except OperationalError as e:
        print(f"   ❌ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error inesperado: {e}")
        return False

def create_missing_tables():
    """Crear tablas faltantes"""
    print(f"\n6. CREACIÓN DE TABLAS:")
    try:
        sys.path.append('.')
        from app.db import engine, Base
        from app import models
        
        Base.metadata.create_all(bind=engine)
        print("   ✅ Tablas creadas/actualizadas exitosamente")
        return True
    except Exception as e:
        print(f"   ❌ Error creando tablas: {e}")
        return False

def main():
    """Función principal"""
    success = diagnose_database()
    
    if success:
        print(f"\n🎯 DIAGNÓSTICO COMPLETADO")
        
        # Preguntar si crear tablas
        response = input("\n¿Crear/actualizar tablas? (y/N): ").strip().lower()
        if response in ['y', 'yes', 'sí', 's']:
            create_missing_tables()
        
        print(f"\n✅ PRÓXIMOS PASOS:")
        print("   1. Verificar que todas las tablas existen")
        print("   2. Ejecutar: python init_db_direct.py (para datos demo)")
        print("   3. Probar API: python test_api.py")
        print("   4. Iniciar aplicación: uvicorn app.main:app --reload")
        
    else:
        print(f"\n❌ DIAGNÓSTICO FALLÓ")
        print("   💡 SOLUCIONES:")
        print("   1. Configurar DATABASE_URL en variables de entorno")
        print("   2. Verificar credenciales de PostgreSQL")
        print("   3. Usar SQLite local: export DATABASE_URL='sqlite:///local.db'")

if __name__ == "__main__":
    main()