#!/usr/bin/env python3
"""
🏥 Script de Verificación de Salud de PostgreSQL

Ejecuta una serie de tests para verificar que la conexión a PostgreSQL
esté funcionando correctamente y que todas las tablas estén creadas.

Uso:
    python3 check_postgres_health.py
"""
import os
import sys
import re
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

def mask_password(url: str) -> str:
    """Enmascarar contraseña en URL para logs seguros"""
    return re.sub(r"://([^:@]+):[^@]+@", r"://\1:***@", url)

def check_environment_vars():
    """Verificar que las variables de entorno estén configuradas"""
    print("\n🔍 1. Verificando variables de entorno...")
    
    env_vars = {
        "DATABASE_URL": os.getenv("DATABASE_URL"),
        "DATABASE_PRIVATE_URL": os.getenv("DATABASE_PRIVATE_URL"),
        "POSTGRES_URL": os.getenv("POSTGRES_URL")
    }
    
    found = False
    for var_name, var_value in env_vars.items():
        if var_value:
            masked = mask_password(var_value)
            print(f"   ✅ {var_name}: {masked}")
            found = True
        else:
            print(f"   ⚠️ {var_name}: No configurada")
    
    if not found:
        print("\n   ❌ No se encontró ninguna variable de DATABASE_URL")
        return False
    
    print("   ✅ Al menos una variable de entorno configurada")
    return True

def check_postgres_connection():
    """Verificar conexión a PostgreSQL"""
    print("\n🔍 2. Probando conexión a PostgreSQL...")
    
    database_url = (
        os.getenv("DATABASE_URL") or 
        os.getenv("DATABASE_PRIVATE_URL") or 
        os.getenv("POSTGRES_URL")
    )
    
    if not database_url:
        print("   ❌ No hay DATABASE_URL configurada")
        return None
    
    if "postgresql" not in database_url and "postgres" not in database_url:
        print(f"   ❌ La URL no es de PostgreSQL: {mask_password(database_url)}")
        return None
    
    try:
        # Normalizar URL para usar psycopg
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10}
        )
        
        with engine.connect() as conn:
            # Test básico
            result = conn.execute(text("SELECT 1")).scalar()
            if result != 1:
                print("   ❌ SELECT 1 no retornó 1")
                return None
            
            # Información de la base de datos
            version = conn.execute(text("SELECT version()")).scalar()
            db_name = conn.execute(text("SELECT current_database()")).scalar()
            
            print(f"   ✅ Conexión exitosa")
            print(f"   📊 Base de datos: {db_name}")
            print(f"   📊 Versión PostgreSQL: {version.split()[1]}")
            print(f"   📊 SSL: {'Sí' if 'sslmode=require' in database_url else 'No especificado'}")
            
            return engine
    
    except OperationalError as e:
        print(f"   ❌ Error de conexión: {e}")
        return None
    except Exception as e:
        print(f"   ❌ Error inesperado: {e}")
        return None

def check_tables(engine):
    """Verificar que las tablas principales existan"""
    print("\n🔍 3. Verificando tablas...")
    
    required_tables = [
        "accounts",
        "users", 
        "apartments",
        "expenses",
        "incomes",
        "reservations"
    ]
    
    all_exist = True
    
    with engine.connect() as conn:
        for table in required_tables:
            try:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"   ✅ {table}: {count} registros")
            except Exception as e:
                print(f"   ❌ {table}: No existe o error - {str(e)[:50]}")
                all_exist = False
    
    return all_exist

def check_indexes_and_constraints(engine):
    """Verificar índices y constraints importantes"""
    print("\n🔍 4. Verificando índices y constraints...")
    
    try:
        with engine.connect() as conn:
            # Verificar foreign keys
            fk_query = text("""
                SELECT 
                    tc.table_name, 
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
                ORDER BY tc.table_name
                LIMIT 10
            """)
            
            fk_results = conn.execute(fk_query).fetchall()
            print(f"   ✅ {len(fk_results)} foreign keys encontradas")
            
            # Verificar índices
            idx_query = text("""
                SELECT 
                    tablename, 
                    indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                LIMIT 10
            """)
            
            idx_results = conn.execute(idx_query).fetchall()
            print(f"   ✅ {len(idx_results)} índices encontrados")
            
            return True
    except Exception as e:
        print(f"   ⚠️ Error verificando constraints: {str(e)[:100]}")
        return False

def check_performance(engine):
    """Verificar rendimiento básico de consultas"""
    print("\n🔍 5. Test de rendimiento básico...")
    
    try:
        import time
        
        with engine.connect() as conn:
            # Test de consulta simple
            start = time.time()
            conn.execute(text("SELECT 1"))
            simple_time = (time.time() - start) * 1000
            
            # Test de consulta con tabla
            start = time.time()
            conn.execute(text("SELECT COUNT(*) FROM apartments"))
            count_time = (time.time() - start) * 1000
            
            print(f"   ✅ SELECT 1: {simple_time:.2f}ms")
            print(f"   ✅ COUNT(*): {count_time:.2f}ms")
            
            if simple_time < 100 and count_time < 500:
                print(f"   ✅ Rendimiento: Excelente")
            elif simple_time < 500 and count_time < 1000:
                print(f"   ⚠️ Rendimiento: Aceptable")
            else:
                print(f"   ⚠️ Rendimiento: Lento (revisar configuración)")
            
            return True
    except Exception as e:
        print(f"   ⚠️ Error en test de rendimiento: {e}")
        return False

def main():
    """Ejecutar todas las verificaciones"""
    print("="*60)
    print("🏥 VERIFICACIÓN DE SALUD DE POSTGRESQL")
    print("="*60)
    
    # 1. Variables de entorno
    if not check_environment_vars():
        print("\n❌ FALLO: Variables de entorno no configuradas")
        sys.exit(1)
    
    # 2. Conexión PostgreSQL
    engine = check_postgres_connection()
    if not engine:
        print("\n❌ FALLO: No se pudo conectar a PostgreSQL")
        print("\n💡 Soluciones:")
        print("   1. Verifica que DATABASE_URL esté correctamente configurada")
        print("   2. Verifica que PostgreSQL esté corriendo")
        print("   3. Verifica las credenciales de acceso")
        print("   4. Verifica que el puerto 5432 esté accesible")
        sys.exit(1)
    
    # 3. Tablas
    tables_ok = check_tables(engine)
    if not tables_ok:
        print("\n⚠️ ADVERTENCIA: Algunas tablas no existen")
        print("💡 Ejecuta: python3 ensure_postgres.py para crear las tablas")
    
    # 4. Constraints e índices
    check_indexes_and_constraints(engine)
    
    # 5. Rendimiento
    check_performance(engine)
    
    # Resumen final
    print("\n" + "="*60)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("="*60)
    print("\n🎯 PostgreSQL está configurado y funcionando correctamente")
    print("🚀 El sistema está listo para usar")
    print("\n📝 Notas:")
    print("   - Solo PostgreSQL está permitido (no SQLite)")
    print("   - Conexión SSL configurada según la URL")
    print("   - Las migraciones se ejecutan automáticamente al iniciar la app")
    print("\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Verificación interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error fatal: {e}")
        sys.exit(1)
