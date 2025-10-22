#!/usr/bin/env python3
"""
Script para inicializar la base de datos con datos de prueba
"""
import requests
import json
from datetime import datetime, timedelta

API_BASE = "https://ses-gastos.onrender.com"
ADMIN_KEY = "test123"  # Cambia esto por tu ADMIN_KEY real

def create_test_data():
    print("🚀 Inicializando base de datos con datos de prueba...")
    
    headers = {
        "Content-Type": "application/json",
        "X-Internal-Key": ADMIN_KEY
    }
    
    # 1. Crear apartamentos
    print("\n1. Creando apartamentos...")
    apartments = [
        {"code": "SES01", "name": "Apartamento Centro", "owner_email": "owner1@sesgas.com"},
        {"code": "SES02", "name": "Apartamento Playa", "owner_email": "owner2@sesgas.com"},
        {"code": "SES03", "name": "Apartamento Montaña", "owner_email": "owner3@sesgas.com"}
    ]
    
    created_apartments = []
    for apt_data in apartments:
        try:
            r = requests.post(f"{API_BASE}/api/v1/apartments/", 
                            json=apt_data, headers=headers, timeout=10)
            if r.status_code in [200, 201]:
                apt = r.json()
                created_apartments.append(apt)
                print(f"   ✅ {apt_data['code']}: {apt.get('id', 'N/A')}")
            else:
                print(f"   ❌ Error creando {apt_data['code']}: {r.status_code} - {r.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    if not created_apartments:
        print("❌ No se pudieron crear apartamentos. Verifica el ADMIN_KEY.")
        return
    
    # 2. Crear gastos de prueba
    print("\n2. Creando gastos de prueba...")
    base_date = datetime.now() - timedelta(days=30)
    
    expenses = [
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
    for i, exp_data in enumerate(expenses):
        try:
            # Distribuir gastos entre apartamentos
            apartment = created_apartments[i % len(created_apartments)]
            
            expense_data = {
                "apartment_id": apartment['id'],
                "date": (base_date + timedelta(days=i*3)).strftime("%Y-%m-%d"),
                "amount_gross": exp_data["amount"],
                "currency": "EUR",
                "category": exp_data["category"],
                "description": exp_data["description"],
                "vendor": exp_data["vendor"],
                "source": "init_script"
            }
            
            r = requests.post(f"{API_BASE}/api/v1/expenses/", 
                            json=expense_data, headers=headers, timeout=10)
            if r.status_code in [200, 201]:
                expense = r.json()
                created_expenses.append(expense)
                print(f"   ✅ €{exp_data['amount']} - {exp_data['vendor']} ({apartment['code']})")
            else:
                print(f"   ❌ Error creando gasto: {r.status_code} - {r.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # 3. Crear ingresos de prueba
    print("\n3. Creando ingresos de prueba...")
    incomes = [
        {"amount": 150.00, "status": "CONFIRMED", "description": "Reserva confirmada - Enero"},
        {"amount": 200.00, "status": "CONFIRMED", "description": "Reserva confirmada - Febrero"},
        {"amount": 180.00, "status": "PENDING", "description": "Reserva pendiente - Marzo"},
        {"amount": 220.00, "status": "CONFIRMED", "description": "Reserva confirmada - Abril"}
    ]
    
    created_incomes = []
    for i, inc_data in enumerate(incomes):
        try:
            apartment = created_apartments[i % len(created_apartments)]
            
            income_data = {
                "apartment_id": apartment['id'],
                "date": (base_date + timedelta(days=i*7)).strftime("%Y-%m-%d"),
                "amount_gross": inc_data["amount"],
                "currency": "EUR",
                "status": inc_data["status"],
                "source": "init_script"
            }
            
            r = requests.post(f"{API_BASE}/api/v1/incomes/", 
                            json=income_data, headers=headers, timeout=10)
            if r.status_code in [200, 201]:
                income = r.json()
                created_incomes.append(income)
                print(f"   ✅ €{inc_data['amount']} - {inc_data['status']} ({apartment['code']})")
            else:
                print(f"   ❌ Error creando ingreso: {r.status_code} - {r.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # 4. Resumen
    print(f"\n📊 RESUMEN:")
    print(f"   ✅ Apartamentos creados: {len(created_apartments)}")
    print(f"   ✅ Gastos creados: {len(created_expenses)}")
    print(f"   ✅ Ingresos creados: {len(created_incomes)}")
    
    if created_apartments and created_expenses:
        print(f"\n🎉 ¡Base de datos inicializada correctamente!")
        print(f"🌐 Dashboard: {API_BASE}/api/v1/dashboard/")
        print(f"🤖 Ahora puedes usar el bot con: /usar {created_apartments[0]['code']}")
    else:
        print(f"\n❌ Hubo problemas inicializando la base de datos.")
        print(f"   Verifica el ADMIN_KEY: {ADMIN_KEY}")

if __name__ == "__main__":
    create_test_data()