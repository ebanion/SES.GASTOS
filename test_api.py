#!/usr/bin/env python3
"""
Script de prueba para verificar la API de SES.GASTOS
"""
import requests
import json
from datetime import datetime

API_BASE = "https://ses-gastos.onrender.com"

def test_api():
    print("🔍 Probando API de SES.GASTOS...")
    
    # 1. Health check
    print("\n1. Health check:")
    try:
        r = requests.get(f"{API_BASE}/health", timeout=10)
        print(f"   Status: {r.status_code}")
        print(f"   Response: {r.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 2. Database status
    print("\n2. Database status:")
    try:
        r = requests.get(f"{API_BASE}/db-status", timeout=10)
        print(f"   Status: {r.status_code}")
        print(f"   Response: {r.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 3. Dashboard health
    print("\n3. Dashboard health:")
    try:
        r = requests.get(f"{API_BASE}/api/v1/dashboard/health", timeout=10)
        print(f"   Status: {r.status_code}")
        print(f"   Response: {r.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 4. List apartments
    print("\n4. Apartamentos existentes:")
    try:
        r = requests.get(f"{API_BASE}/api/v1/apartments/", timeout=10)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            apartments = r.json()
            print(f"   Apartamentos encontrados: {len(apartments)}")
            for apt in apartments:
                print(f"     - {apt.get('code', 'N/A')}: {apt.get('name', 'N/A')}")
        else:
            print(f"   Error response: {r.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 5. List expenses
    print("\n5. Gastos existentes:")
    try:
        r = requests.get(f"{API_BASE}/api/v1/expenses/", timeout=10)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            expenses = r.json()
            print(f"   Gastos encontrados: {len(expenses)}")
            for exp in expenses[:3]:  # Solo primeros 3
                print(f"     - {exp.get('date', 'N/A')}: €{exp.get('amount_gross', 0)} - {exp.get('description', 'N/A')}")
        else:
            print(f"   Error response: {r.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 6. Create test apartment if none exist
    print("\n6. Crear apartamento de prueba:")
    try:
        apartment_data = {
            "code": "SES01",
            "name": "Apartamento SES01 - Prueba",
            "owner_email": "test@sesgas.com"
        }
        r = requests.post(f"{API_BASE}/api/v1/apartments/", 
                         json=apartment_data, timeout=10)
        print(f"   Status: {r.status_code}")
        if r.status_code in [200, 201]:
            print(f"   ✅ Apartamento creado: {r.json()}")
        else:
            print(f"   Response: {r.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 7. Create test expense
    print("\n7. Crear gasto de prueba:")
    try:
        # First get apartment ID
        r_apt = requests.get(f"{API_BASE}/api/v1/apartments/", timeout=10)
        if r_apt.status_code == 200:
            apartments = r_apt.json()
            if apartments:
                apt_id = apartments[0].get('id')
                expense_data = {
                    "apartment_id": apt_id,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "amount_gross": 42.50,
                    "currency": "EUR",
                    "category": "Prueba",
                    "description": "Gasto de prueba desde script",
                    "vendor": "Vendor Test",
                    "source": "test_script"
                }
                r = requests.post(f"{API_BASE}/api/v1/expenses/", 
                                 json=expense_data, timeout=10)
                print(f"   Status: {r.status_code}")
                if r.status_code in [200, 201]:
                    print(f"   ✅ Gasto creado: {r.json()}")
                else:
                    print(f"   Response: {r.text}")
            else:
                print("   ❌ No hay apartamentos disponibles")
        else:
            print("   ❌ No se pudieron obtener apartamentos")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n✅ Prueba completada!")
    print(f"🌐 Dashboard: {API_BASE}/api/v1/dashboard/")

if __name__ == "__main__":
    test_api()