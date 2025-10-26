#!/usr/bin/env python3
"""
Script de migración segura para actualizar la base de datos
"""
import sys
import os
from datetime import datetime

sys.path.append('.')

def backup_sqlite_if_exists():
    """Hacer backup de SQLite si existe"""
    sqlite_files = ['local.db', 'ses_gastos.db', '/tmp/ses_gastos.db']
    backups_made = []
    
    for db_file in sqlite_files:
        if os.path.exists(db_file):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"{db_file}.backup_{timestamp}"
            
            try:
                import shutil
                shutil.copy2(db_file, backup_file)
                backups_made.append(backup_file)
                print(f"✅ Backup creado: {backup_file}")
            except Exception as e:
                print(f"⚠️ Error creando backup de {db_file}: {e}")
    
    return backups_made

def migrate_income_ids():
    """Migrar IDs de Income de UUID a String si es necesario"""
    try:
        from app.db import SessionLocal, engine
        from sqlalchemy import text, inspect
        
        # Verificar si la tabla incomes existe y su estructura
        inspector = inspect(engine)
        if 'incomes' not in inspector.get_table_names():
            print("ℹ️ Tabla incomes no existe, se creará con la estructura correcta")
            return True
        
        # Verificar el tipo de columna ID
        columns = inspector.get_columns('incomes')
        id_column = next((col for col in columns if col['name'] == 'id'), None)
        
        if id_column:
            print(f"ℹ️ Columna ID actual: {id_column['type']}")
            
            # Si es UUID, necesitamos migrar (solo en PostgreSQL)
            if "postgresql" in str(engine.url) and 'uuid' in str(id_column['type']).lower():
                print("🔄 Migrando IDs de UUID a VARCHAR(36)...")
                
                with engine.connect() as conn:
                    # Crear tabla temporal
                    conn.execute(text("""
                        CREATE TABLE incomes_temp AS 
                        SELECT 
                            id::text as id,
                            apartment_id,
                            reservation_id,
                            date,
                            amount_gross,
                            currency,
                            status,
                            non_refundable_at,
                            source,
                            guest_name,
                            guest_email,
                            booking_reference,
                            check_in_date,
                            check_out_date,
                            guests_count,
                            email_message_id,
                            processed_from_email,
                            created_at,
                            updated_at
                        FROM incomes
                    """))
                    
                    # Eliminar tabla original
                    conn.execute(text("DROP TABLE incomes"))
                    
                    # Renombrar tabla temporal
                    conn.execute(text("ALTER TABLE incomes_temp RENAME TO incomes"))
                    
                    # Recrear constraints
                    conn.execute(text("""
                        ALTER TABLE incomes 
                        ADD CONSTRAINT incomes_pkey PRIMARY KEY (id)
                    """))
                    
                    conn.commit()
                    print("✅ Migración de IDs completada")
            else:
                print("✅ IDs ya están en formato correcto")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en migración de IDs: {e}")
        return False

def verify_database_structure():
    """Verificar que la estructura de la base de datos sea correcta"""
    try:
        from app.db import SessionLocal, test_connection, create_tables
        from app import models
        
        print("🔍 Verificando estructura de base de datos...")
        
        if not test_connection():
            print("❌ Error de conexión a base de datos")
            return False
        
        # Crear/actualizar tablas
        if not create_tables():
            print("❌ Error creando tablas")
            return False
        
        # Verificar que podemos crear instancias de todos los modelos
        db = SessionLocal()
        try:
            # Test de modelos principales
            models_to_test = [
                models.User,
                models.Apartment, 
                models.Expense,
                models.Income,
                models.Reservation,
                models.IdempotencyKey
            ]
            
            for model in models_to_test:
                count = db.query(model).count()
                print(f"✅ {model.__tablename__}: {count} registros")
            
            return True
            
        except Exception as e:
            print(f"❌ Error verificando modelos: {e}")
            return False
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error verificando estructura: {e}")
        return False

def create_sample_data():
    """Crear datos de muestra si no existen"""
    try:
        from app.db import SessionLocal
        from app import models
        from datetime import date, timedelta
        
        db = SessionLocal()
        try:
            # Verificar si ya hay datos
            apartments_count = db.query(models.Apartment).count()
            
            if apartments_count == 0:
                print("📝 Creando datos de muestra...")
                
                # Crear apartamento
                apartment = models.Apartment(
                    code="SES01",
                    name="Apartamento Demo",
                    owner_email="demo@sesgas.com",
                    is_active=True
                )
                db.add(apartment)
                db.flush()
                
                # Crear gasto
                expense = models.Expense(
                    apartment_id=apartment.id,
                    date=date.today(),
                    amount_gross=50.00,
                    currency="EUR",
                    category="Demo",
                    description="Gasto de demostración",
                    vendor="Vendor Demo",
                    source="migration_script"
                )
                db.add(expense)
                
                # Crear ingreso
                income = models.Income(
                    apartment_id=apartment.id,
                    date=date.today(),
                    amount_gross=100.00,
                    currency="EUR",
                    status="CONFIRMED",
                    source="migration_demo",
                    guest_name="Cliente Demo",
                    guest_email="demo@example.com"
                )
                db.add(income)
                
                db.commit()
                print("✅ Datos de muestra creados")
            else:
                print(f"ℹ️ Ya existen {apartments_count} apartamentos")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error creando datos de muestra: {e}")
        return False

def main():
    """Función principal de migración"""
    print("🔄 MIGRACIÓN SEGURA DE BASE DE DATOS - SES.GASTOS")
    print("=" * 60)
    
    # 1. Backup
    print("\n1. CREANDO BACKUPS...")
    backups = backup_sqlite_if_exists()
    if backups:
        print(f"✅ {len(backups)} backups creados")
    
    # 2. Migrar IDs si es necesario
    print("\n2. MIGRANDO ESTRUCTURA...")
    if not migrate_income_ids():
        print("❌ Error en migración de IDs")
        return False
    
    # 3. Verificar estructura
    print("\n3. VERIFICANDO ESTRUCTURA...")
    if not verify_database_structure():
        print("❌ Error verificando estructura")
        return False
    
    # 4. Crear datos de muestra
    print("\n4. VERIFICANDO DATOS...")
    if not create_sample_data():
        print("❌ Error creando datos de muestra")
        return False
    
    print("\n✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
    print("\n🎯 PRÓXIMOS PASOS:")
    print("   1. Ejecutar: python test_api.py")
    print("   2. Iniciar aplicación: uvicorn app.main:app --reload")
    print("   3. Verificar dashboard: http://localhost:8000/api/v1/dashboard/")
    
    if backups:
        print(f"\n💾 BACKUPS DISPONIBLES:")
        for backup in backups:
            print(f"   - {backup}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)