#!/usr/bin/env python3
"""
Script para inicializar la base de datos directamente con SQLAlchemy
"""
import sys
import os
sys.path.append('.')

def init_database():
    print("🚀 Inicializando base de datos directamente...")
    
    # Importar después de configurar el path
    from app.db import SessionLocal, engine, test_connection, create_tables
    from app import models
    from datetime import datetime, timedelta
    
    # Verificar conexión
    if not test_connection():
        print("❌ Error: No se puede conectar a la base de datos")
        return False
    
    # Crear tablas
    if not create_tables():
        print("❌ Error: No se pudieron crear las tablas")
        return False
    
    db = SessionLocal()
    try:
        # 1. Verificar si ya hay apartamentos
        existing_apartments = db.query(models.Apartment).count()
        if existing_apartments > 0:
            print(f"   ℹ️  Ya hay {existing_apartments} apartamentos en la BD")
        else:
            # Crear apartamentos
            print("\n1. Creando apartamentos...")
            apartments_data = [
                {"code": "SES01", "name": "Apartamento Centro", "owner_email": "owner1@sesgas.com"},
                {"code": "SES02", "name": "Apartamento Playa", "owner_email": "owner2@sesgas.com"},
                {"code": "SES03", "name": "Apartamento Montaña", "owner_email": "owner3@sesgas.com"}
            ]
            
            created_apartments = []
            for apt_data in apartments_data:
                apt = models.Apartment(
                    code=apt_data["code"],
                    name=apt_data["name"],
                    owner_email=apt_data["owner_email"],
                    is_active=True
                )
                db.add(apt)
                created_apartments.append(apt)
                print(f"   ✅ {apt_data['code']}")
            
            db.commit()
            
            # Refresh para obtener IDs
            for apt in created_apartments:
                db.refresh(apt)
        
        # Obtener apartamentos existentes
        apartments = db.query(models.Apartment).all()
        print(f"\n📋 Apartamentos disponibles: {len(apartments)}")
        for apt in apartments:
            print(f"   - {apt.code} (ID: {apt.id})")
        
        # 2. Verificar gastos existentes
        existing_expenses = db.query(models.Expense).count()
        if existing_expenses > 0:
            print(f"\n   ℹ️  Ya hay {existing_expenses} gastos en la BD")
        else:
            # Crear gastos de prueba
            print("\n2. Creando gastos de prueba...")
            base_date = datetime.now() - timedelta(days=30)
            
            expenses_data = [
                {"amount": 45.50, "category": "Restauración", "vendor": "Restaurante El Buen Comer", "description": "Cena de negocios"},
                {"amount": 25.00, "category": "Transporte", "vendor": "Taxi Madrid", "description": "Traslado aeropuerto"},
                {"amount": 120.75, "category": "Alojamiento", "vendor": "Hotel Central", "description": "Noche extra huésped"},
                {"amount": 15.30, "category": "Alimentación", "vendor": "Supermercado Local", "description": "Compra semanal"},
                {"amount": 80.00, "category": "Servicios", "vendor": "Electricista Rápido", "description": "Reparación enchufe"},
                {"amount": 35.20, "category": "Limpieza", "vendor": "Limpieza Express", "description": "Limpieza profunda"},
                {"amount": 60.00, "category": "Mantenimiento", "vendor": "Fontanero Pro", "description": "Reparación grifo"},
                {"amount": 22.50, "category": "Restauración", "vendor": "Pizzería Italiana", "description": "Almuerzo equipo"}
            ]
            
            created_expenses = []
            for i, exp_data in enumerate(expenses_data):
                apartment = apartments[i % len(apartments)]
                
                expense = models.Expense(
                    apartment_id=apartment.id,
                    date=(base_date + timedelta(days=i*3)).date(),
                    amount_gross=exp_data["amount"],
                    currency="EUR",
                    category=exp_data["category"],
                    description=exp_data["description"],
                    vendor=exp_data["vendor"],
                    source="init_script"
                )
                db.add(expense)
                created_expenses.append(expense)
                print(f"   ✅ €{exp_data['amount']} - {exp_data['vendor']} ({apartment.code})")
            
            db.commit()
        
        # 3. Verificar ingresos existentes
        existing_incomes = db.query(models.Income).count()
        if existing_incomes > 0:
            print(f"\n   ℹ️  Ya hay {existing_incomes} ingresos en la BD")
        else:
            # Crear ingresos de prueba
            print("\n3. Creando ingresos de prueba...")
            incomes_data = [
                {"amount": 150.00, "status": "CONFIRMED", "description": "Reserva confirmada - Enero"},
                {"amount": 200.00, "status": "CONFIRMED", "description": "Reserva confirmada - Febrero"},
                {"amount": 180.00, "status": "PENDING", "description": "Reserva pendiente - Marzo"},
                {"amount": 220.00, "status": "CONFIRMED", "description": "Reserva confirmada - Abril"}
            ]
            
            created_incomes = []
            for i, inc_data in enumerate(incomes_data):
                apartment = apartments[i % len(apartments)]
                
                income = models.Income(
                    apartment_id=apartment.id,
                    date=(base_date + timedelta(days=i*7)).date(),
                    amount_gross=inc_data["amount"],
                    currency="EUR",
                    status=inc_data["status"],
                    source="init_script"
                )
                db.add(income)
                created_incomes.append(income)
                print(f"   ✅ €{inc_data['amount']} - {inc_data['status']} ({apartment.code})")
            
            db.commit()
        
        # 4. Resumen final
        final_apartments = db.query(models.Apartment).count()
        final_expenses = db.query(models.Expense).count()
        final_incomes = db.query(models.Income).count()
        
        print(f"\n📊 ESTADO FINAL DE LA BASE DE DATOS:")
        print(f"   ✅ Apartamentos: {final_apartments}")
        print(f"   ✅ Gastos: {final_expenses}")
        print(f"   ✅ Ingresos: {final_incomes}")
        
        if final_apartments > 0:
            print(f"\n🎉 ¡Base de datos inicializada correctamente!")
            print(f"🌐 Dashboard: https://ses-gastos.onrender.com/api/v1/dashboard/")
            print(f"🤖 Ahora puedes usar el bot con: /usar {apartments[0].code}")
            
            print(f"\n📱 PASOS PARA USAR EL BOT:")
            print(f"1. Ejecuta el bot: python app/bot/Telegram_expense_bot.py")
            print(f"2. En Telegram: /start")
            print(f"3. Configura apartamento: /usar {apartments[0].code}")
            print(f"4. Envía una foto de factura 📸")
            print(f"5. ¡El gasto aparecerá en el dashboard! 🎊")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()