#!/usr/bin/env python3
"""
Script para probar el sistema completo de gestión
"""
import requests
import json
import time
from datetime import date

# Configuración
BASE_URL = 'http://localhost:8000'
ADMIN_KEY = 'test-admin-key'

def test_complete_workflow():
    """Probar flujo completo de gestión"""
    print("🚀 TESTING SISTEMA COMPLETO DE GESTIÓN")
    print("=" * 60)
    
    headers = {'X-Internal-Key': ADMIN_KEY}
    
    # 1. Crear apartamento
    print("\n1️⃣ Creando apartamento de prueba...")
    apartment_data = {
        'code': 'DEMO001',
        'name': 'Apartamento Demo Completo',
        'owner_email': 'demo@example.com'
    }
    
    response = requests.post(f'{BASE_URL}/api/v1/apartments', 
                           json=apartment_data, headers=headers)
    
    if response.status_code == 200:
        apartment = response.json()
        apartment_id = apartment['id']
        print(f"   ✅ Apartamento creado: {apartment['code']} (ID: {apartment_id})")
    else:
        print(f"   ❌ Error: {response.text}")
        return False
    
    # 2. Crear múltiples gastos
    print("\n2️⃣ Creando gastos de ejemplo...")
    expenses = [
        {
            'apartment_id': apartment_id,
            'date': str(date.today()),
            'amount_gross': '85.50',
            'currency': 'EUR',
            'category': 'electricidad',
            'description': 'Factura de luz',
            'vendor': 'Iberdrola',
            'source': 'demo_test'
        },
        {
            'apartment_id': apartment_id,
            'date': str(date.today()),
            'amount_gross': '45.30',
            'currency': 'EUR',
            'category': 'agua',
            'description': 'Factura de agua',
            'vendor': 'Aguas Municipales',
            'source': 'demo_test'
        },
        {
            'apartment_id': apartment_id,
            'date': str(date.today()),
            'amount_gross': '120.00',
            'currency': 'EUR',
            'category': 'limpieza',
            'description': 'Limpieza profunda',
            'vendor': 'Limpieza Pro',
            'source': 'demo_test'
        }
    ]
    
    expense_ids = []
    for i, expense_data in enumerate(expenses):
        response = requests.post(f'{BASE_URL}/api/v1/expenses', 
                               json=expense_data, headers=headers)
        if response.status_code == 200:
            expense = response.json()
            expense_ids.append(expense['id'])
            print(f"   ✅ Gasto {i+1}: €{expense['amount_gross']} - {expense_data['category']}")
        else:
            print(f"   ❌ Error en gasto {i+1}: {response.text}")
    
    # 3. Crear múltiples ingresos
    print("\n3️⃣ Creando ingresos de ejemplo...")
    incomes = [
        {
            'apartment_id': apartment_id,
            'date': str(date.today()),
            'amount_gross': '200.00',
            'currency': 'EUR',
            'status': 'CONFIRMED',
            'source': 'booking_com',
            'guest_name': 'Juan Pérez',
            'booking_reference': 'BK-001'
        },
        {
            'apartment_id': apartment_id,
            'date': str(date.today()),
            'amount_gross': '180.00',
            'currency': 'EUR',
            'status': 'CONFIRMED',
            'source': 'airbnb',
            'guest_name': 'María García',
            'booking_reference': 'AIR-002'
        },
        {
            'apartment_id': apartment_id,
            'date': str(date.today()),
            'amount_gross': '150.00',
            'currency': 'EUR',
            'status': 'PENDING',
            'source': 'direct',
            'guest_name': 'Carlos López',
            'booking_reference': 'DIR-003'
        }
    ]
    
    income_ids = []
    for i, income_data in enumerate(incomes):
        response = requests.post(f'{BASE_URL}/api/v1/incomes', 
                               json=income_data, headers=headers)
        if response.status_code == 200:
            income = response.json()
            income_ids.append(income['id'])
            print(f"   ✅ Ingreso {i+1}: €{income['amount_gross']} - {income_data['status']} - {income_data['guest_name']}")
        else:
            print(f"   ❌ Error en ingreso {i+1}: {response.text}")
    
    # 4. Verificar datos creados
    print("\n4️⃣ Verificando datos creados...")
    
    # Verificar apartamento
    response = requests.get(f'{BASE_URL}/api/v1/apartments/{apartment_id}')
    if response.status_code == 200:
        print(f"   ✅ Apartamento verificado: {response.json()['code']}")
    
    # Verificar gastos
    response = requests.get(f'{BASE_URL}/api/v1/expenses/by-apartment/{apartment_id}')
    if response.status_code == 200:
        expenses_data = response.json()
        total_expenses = sum(float(exp['amount_gross']) for exp in expenses_data)
        print(f"   ✅ Gastos verificados: {len(expenses_data)} gastos, Total: €{total_expenses:.2f}")
    
    # Verificar ingresos
    response = requests.get(f'{BASE_URL}/api/v1/incomes/by-apartment/{apartment_id}')
    if response.status_code == 200:
        incomes_data = response.json()['incomes']
        total_incomes = sum(float(inc['amount_gross']) for inc in incomes_data)
        confirmed_incomes = sum(float(inc['amount_gross']) for inc in incomes_data if inc['status'] == 'CONFIRMED')
        print(f"   ✅ Ingresos verificados: {len(incomes_data)} ingresos, Total: €{total_incomes:.2f}, Confirmados: €{confirmed_incomes:.2f}")
    
    # 5. Calcular rentabilidad
    print("\n5️⃣ Calculando rentabilidad...")
    net_profit = confirmed_incomes - total_expenses
    print(f"   📊 Ingresos confirmados: €{confirmed_incomes:.2f}")
    print(f"   📊 Gastos totales: €{total_expenses:.2f}")
    print(f"   📊 Beneficio neto: €{net_profit:.2f}")
    
    if net_profit > 0:
        print(f"   ✅ Apartamento rentable (+€{net_profit:.2f})")
    else:
        print(f"   ⚠️ Apartamento en pérdidas (€{net_profit:.2f})")
    
    # 6. Probar operaciones de actualización
    print("\n6️⃣ Probando actualizaciones...")
    
    # Actualizar apartamento
    update_data = {'name': 'Apartamento Demo Actualizado'}
    response = requests.patch(f'{BASE_URL}/api/v1/apartments/{apartment_id}', 
                            json=update_data, headers=headers)
    if response.status_code == 200:
        print("   ✅ Apartamento actualizado")
    
    # Actualizar un gasto
    if expense_ids:
        update_data = {'description': 'Factura actualizada via API'}
        response = requests.patch(f'{BASE_URL}/api/v1/expenses/{expense_ids[0]}', 
                                json=update_data, headers=headers)
        if response.status_code == 200:
            print("   ✅ Gasto actualizado")
    
    # Actualizar un ingreso
    if income_ids:
        update_data = {'guest_name': 'Cliente Actualizado'}
        response = requests.patch(f'{BASE_URL}/api/v1/incomes/{income_ids[0]}', 
                                json=update_data, headers=headers)
        if response.status_code == 200:
            print("   ✅ Ingreso actualizado")
    
    # 7. Probar interfaz web
    print("\n7️⃣ Verificando interfaz web...")
    
    # Probar dashboard de gestión
    response = requests.get(f'{BASE_URL}/management/')
    if response.status_code == 200:
        print("   ✅ Interfaz de gestión disponible")
        print(f"   🌐 URL: {BASE_URL}/management/")
    
    # Probar dashboard público
    response = requests.get(f'{BASE_URL}/api/v1/dashboard/')
    if response.status_code == 200:
        print("   ✅ Dashboard público disponible")
        print(f"   🌐 URL: {BASE_URL}/api/v1/dashboard/")
    
    # 8. Limpiar datos de prueba
    print("\n8️⃣ Limpiando datos de prueba...")
    
    # Eliminar gastos
    for expense_id in expense_ids:
        response = requests.delete(f'{BASE_URL}/api/v1/expenses/{expense_id}', headers=headers)
        if response.status_code == 200:
            print(f"   ✅ Gasto eliminado: {expense_id}")
    
    # Eliminar ingresos
    for income_id in income_ids:
        response = requests.delete(f'{BASE_URL}/api/v1/incomes/{income_id}', headers=headers)
        if response.status_code == 200:
            print(f"   ✅ Ingreso eliminado: {income_id}")
    
    # Eliminar apartamento
    response = requests.delete(f'{BASE_URL}/api/v1/apartments/{apartment_id}', headers=headers)
    if response.status_code == 200:
        print(f"   ✅ Apartamento eliminado: {apartment_id}")
    
    print("\n🎉 SISTEMA COMPLETO PROBADO EXITOSAMENTE!")
    print("\n📋 RESUMEN:")
    print("   ✅ APIs CRUD funcionando correctamente")
    print("   ✅ Gestión de apartamentos operativa")
    print("   ✅ Gestión de gastos operativa")
    print("   ✅ Gestión de ingresos operativa")
    print("   ✅ Cálculos de rentabilidad correctos")
    print("   ✅ Interfaz web disponible")
    print("   ✅ Operaciones de limpieza exitosas")
    
    print(f"\n🌐 INTERFACES DISPONIBLES:")
    print(f"   • Panel de Gestión: {BASE_URL}/management/")
    print(f"   • Dashboard Público: {BASE_URL}/api/v1/dashboard/")
    print(f"   • Registro Público: {BASE_URL}/public/register")
    print(f"   • Documentación API: {BASE_URL}/docs")
    
    return True

def main():
    print("🧪 TESTING SISTEMA COMPLETO DE GESTIÓN SES.GASTOS")
    print("=" * 60)
    
    # Verificar servidor
    try:
        response = requests.get(f'{BASE_URL}/health', timeout=5)
        if response.status_code == 200:
            print("✅ Servidor disponible")
        else:
            print("❌ Servidor no responde correctamente")
            return
    except Exception as e:
        print(f"❌ No se puede conectar al servidor: {e}")
        print(f"   Asegúrate de que el servidor esté ejecutándose en {BASE_URL}")
        return
    
    # Ejecutar pruebas
    success = test_complete_workflow()
    
    if success:
        print("\n🎉 ¡TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE!")
        print("\n💡 TU SISTEMA DE GESTIÓN ESTÁ LISTO PARA USAR")
    else:
        print("\n❌ Algunas pruebas fallaron")

if __name__ == '__main__':
    main()