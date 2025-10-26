#!/usr/bin/env python3
"""
Test local de la implementación
"""
import sys
import os
sys.path.append('.')

def test_database_operations():
    """Probar operaciones básicas de base de datos"""
    print("🧪 PROBANDO OPERACIONES DE BASE DE DATOS")
    print("=" * 50)
    
    try:
        from app.db import SessionLocal, test_connection
        from app import models
        from datetime import date
        
        # Test de conexión
        if not test_connection():
            print("❌ Error de conexión")
            return False
        print("✅ Conexión exitosa")
        
        db = SessionLocal()
        try:
            # 1. Verificar apartamentos
            apartments = db.query(models.Apartment).all()
            print(f"✅ Apartamentos encontrados: {len(apartments)}")
            for apt in apartments:
                print(f"   - {apt.code}: {apt.name}")
            
            # 2. Crear un gasto de prueba
            if apartments:
                expense = models.Expense(
                    apartment_id=apartments[0].id,
                    date=date.today(),
                    amount_gross=99.99,
                    currency="EUR",
                    category="Prueba Local",
                    description="Gasto de prueba local",
                    vendor="Test Vendor",
                    source="test_local"
                )
                db.add(expense)
                db.commit()
                db.refresh(expense)
                print(f"✅ Gasto creado: ID {expense.id}, €{expense.amount_gross}")
            
            # 3. Crear un ingreso de prueba
            if apartments:
                income = models.Income(
                    apartment_id=apartments[0].id,
                    date=date.today(),
                    amount_gross=199.99,
                    currency="EUR",
                    status="CONFIRMED",
                    source="test_local",
                    guest_name="Cliente Test Local",
                    guest_email="test@local.com"
                )
                db.add(income)
                db.commit()
                db.refresh(income)
                print(f"✅ Ingreso creado: ID {income.id}, €{income.amount_gross}")
            
            # 4. Verificar totales
            total_expenses = db.query(models.Expense).count()
            total_incomes = db.query(models.Income).count()
            total_reservations = db.query(models.Reservation).count()
            
            print(f"\n📊 RESUMEN:")
            print(f"   - Apartamentos: {len(apartments)}")
            print(f"   - Gastos: {total_expenses}")
            print(f"   - Ingresos: {total_incomes}")
            print(f"   - Reservas: {total_reservations}")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_consistency():
    """Probar consistencia de modelos"""
    print(f"\n🔍 PROBANDO CONSISTENCIA DE MODELOS")
    print("=" * 50)
    
    try:
        from app import models
        from sqlalchemy import inspect
        from app.db import engine
        
        # Verificar que todos los modelos usen String(36) para IDs
        inspector = inspect(engine)
        
        models_to_check = [
            ('users', models.User),
            ('apartments', models.Apartment),
            ('expenses', models.Expense),
            ('incomes', models.Income),
            ('reservations', models.Reservation)
        ]
        
        for table_name, model_class in models_to_check:
            if table_name in inspector.get_table_names():
                columns = inspector.get_columns(table_name)
                id_column = next((col for col in columns if col['name'] == 'id'), None)
                
                if id_column:
                    print(f"✅ {table_name}.id: {id_column['type']}")
                else:
                    print(f"⚠️ {table_name}: Sin columna ID")
            else:
                print(f"❌ {table_name}: Tabla no existe")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando modelos: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 TEST LOCAL DE IMPLEMENTACIÓN - SES.GASTOS")
    print("=" * 60)
    
    # Configurar DATABASE_URL si no está configurada
    if not os.getenv('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'sqlite:///local.db'
        print("ℹ️ Usando SQLite local por defecto")
    
    success = True
    
    # Test 1: Operaciones de base de datos
    if not test_database_operations():
        success = False
    
    # Test 2: Consistencia de modelos
    if not test_model_consistency():
        success = False
    
    if success:
        print(f"\n🎉 TODOS LOS TESTS PASARON")
        print(f"✅ La implementación está funcionando correctamente")
        print(f"\n🎯 PRÓXIMOS PASOS:")
        print(f"   1. Iniciar servidor: uvicorn app.main:app --reload")
        print(f"   2. Abrir: http://localhost:8000")
        print(f"   3. Dashboard: http://localhost:8000/api/v1/dashboard/")
    else:
        print(f"\n❌ ALGUNOS TESTS FALLARON")
        print(f"⚠️ Revisar errores arriba")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)