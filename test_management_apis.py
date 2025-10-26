#!/usr/bin/env python3
"""
Script para probar las APIs de gestión (CRUD) del sistema
"""
import requests
import json
import os
from datetime import date, datetime
from decimal import Decimal

# Configuración
BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
ADMIN_KEY = os.getenv('ADMIN_KEY', 'test-admin-key')

def test_server_health():
    """Verificar que el servidor esté funcionando"""
    try:
        response = requests.get(f'{BASE_URL}/health', timeout=5)
        print(f'✅ Servidor: {response.status_code} - {response.json()}')
        return True
    except Exception as e:
        print(f'❌ Servidor no disponible: {e}')
        return False

def test_apartments_crud():
    """Probar CRUD de apartamentos"""
    print('\n🏠 TESTING APARTAMENTOS CRUD')
    print('-' * 40)
    
    headers = {'X-Internal-Key': ADMIN_KEY}
    
    # 1. Crear apartamento
    print('1. Creando apartamento...')
    apartment_data = {
        'code': 'TEST001',
        'name': 'Apartamento Test',
        'owner_email': 'test@example.com'
    }
    
    try:
        response = requests.post(f'{BASE_URL}/api/v1/apartments', 
                               json=apartment_data, headers=headers)
        print(f'   Status: {response.status_code}')
        if response.status_code == 201 or response.status_code == 200:
            apt_data = response.json()
            apartment_id = apt_data['id']
            print(f'   ✅ Apartamento creado: {apartment_id}')
        else:
            print(f'   ❌ Error: {response.text}')
            return None
    except Exception as e:
        print(f'   ❌ Error de conexión: {e}')
        return None
    
    # 2. Listar apartamentos
    print('2. Listando apartamentos...')
    try:
        response = requests.get(f'{BASE_URL}/api/v1/apartments')
        print(f'   Status: {response.status_code}')
        if response.status_code == 200:
            apartments = response.json()
            print(f'   ✅ Total apartamentos: {len(apartments)}')
        else:
            print(f'   ❌ Error: {response.text}')
    except Exception as e:
        print(f'   ❌ Error: {e}')
    
    # 3. Obtener apartamento por ID
    print('3. Obteniendo apartamento por ID...')
    try:
        response = requests.get(f'{BASE_URL}/api/v1/apartments/{apartment_id}')
        print(f'   Status: {response.status_code}')
        if response.status_code == 200:
            apt = response.json()
            print(f'   ✅ Apartamento: {apt["code"]} - {apt["name"]}')
        else:
            print(f'   ❌ Error: {response.text}')
    except Exception as e:
        print(f'   ❌ Error: {e}')
    
    # 4. Actualizar apartamento
    print('4. Actualizando apartamento...')
    update_data = {'name': 'Apartamento Test Actualizado'}
    try:
        response = requests.patch(f'{BASE_URL}/api/v1/apartments/{apartment_id}', 
                                json=update_data, headers=headers)
        print(f'   Status: {response.status_code}')
        if response.status_code == 200:
            print(f'   ✅ Apartamento actualizado')
        else:
            print(f'   ❌ Error: {response.text}')
    except Exception as e:
        print(f'   ❌ Error: {e}')
    
    return apartment_id

def test_expenses_crud(apartment_id):
    """Probar CRUD de gastos"""
    print('\n💰 TESTING GASTOS CRUD')
    print('-' * 40)
    
    if not apartment_id:
        print('❌ No hay apartamento para probar gastos')
        return None
    
    headers = {'X-Internal-Key': ADMIN_KEY}
    
    # 1. Crear gasto
    print('1. Creando gasto...')
    expense_data = {
        'apartment_id': apartment_id,
        'date': str(date.today()),
        'amount_gross': '45.50',
        'currency': 'EUR',
        'category': 'test',
        'description': 'Gasto de prueba',
        'vendor': 'Vendor Test',
        'source': 'test_api'
    }
    
    try:
        response = requests.post(f'{BASE_URL}/api/v1/expenses', 
                               json=expense_data, headers=headers)
        print(f'   Status: {response.status_code}')
        if response.status_code == 201 or response.status_code == 200:
            expense = response.json()
            expense_id = expense['id']
            print(f'   ✅ Gasto creado: {expense_id}')
        else:
            print(f'   ❌ Error: {response.text}')
            return None
    except Exception as e:
        print(f'   ❌ Error: {e}')
        return None
    
    # 2. Listar gastos
    print('2. Listando gastos...')
    try:
        response = requests.get(f'{BASE_URL}/api/v1/expenses')
        print(f'   Status: {response.status_code}')
        if response.status_code == 200:
            expenses = response.json()
            print(f'   ✅ Total gastos: {len(expenses)}')
        else:
            print(f'   ❌ Error: {response.text}')
    except Exception as e:
        print(f'   ❌ Error: {e}')
    
    # 3. Obtener gasto por ID
    print('3. Obteniendo gasto por ID...')
    try:
        response = requests.get(f'{BASE_URL}/api/v1/expenses/{expense_id}')
        print(f'   Status: {response.status_code}')
        if response.status_code == 200:
            expense = response.json()
            print(f'   ✅ Gasto: {expense["amount_gross"]} {expense["currency"]} - {expense["description"]}')
        else:
            print(f'   ❌ Error: {response.text}')
    except Exception as e:
        print(f'   ❌ Error: {e}')
    
    # 4. Actualizar gasto (PATCH)
    print('4. Actualizando gasto...')
    update_data = {'description': 'Gasto actualizado via API'}
    try:
        response = requests.patch(f'{BASE_URL}/api/v1/expenses/{expense_id}', 
                                json=update_data, headers=headers)
        print(f'   Status: {response.status_code}')
        if response.status_code == 200:
            print(f'   ✅ Gasto actualizado')
        else:
            print(f'   ❌ Error: {response.text}')
    except Exception as e:
        print(f'   ❌ Error: {e}')
    
    return expense_id

def test_incomes_crud(apartment_id):
    """Probar CRUD de ingresos"""
    print('\n💵 TESTING INGRESOS CRUD')
    print('-' * 40)
    
    if not apartment_id:
        print('❌ No hay apartamento para probar ingresos')
        return None
    
    headers = {'X-Internal-Key': ADMIN_KEY}
    
    # 1. Crear ingreso
    print('1. Creando ingreso...')
    income_data = {
        'apartment_id': apartment_id,
        'date': str(date.today()),
        'amount_gross': '150.00',
        'currency': 'EUR',
        'status': 'CONFIRMED',
        'source': 'test_api',
        'guest_name': 'Cliente Test',
        'guest_email': 'cliente@test.com',
        'booking_reference': 'TEST-001'
    }
    
    try:
        response = requests.post(f'{BASE_URL}/api/v1/incomes', 
                               json=income_data, headers=headers)
        print(f'   Status: {response.status_code}')
        if response.status_code == 201 or response.status_code == 200:
            income = response.json()
            income_id = income['id']
            print(f'   ✅ Ingreso creado: {income_id}')
        else:
            print(f'   ❌ Error: {response.text}')
            return None
    except Exception as e:
        print(f'   ❌ Error: {e}')
        return None
    
    # 2. Listar ingresos
    print('2. Listando ingresos...')
    try:
        response = requests.get(f'{BASE_URL}/api/v1/incomes')
        print(f'   Status: {response.status_code}')
        if response.status_code == 200:
            incomes = response.json()
            print(f'   ✅ Total ingresos: {len(incomes)}')
        else:
            print(f'   ❌ Error: {response.text}')
    except Exception as e:
        print(f'   ❌ Error: {e}')
    
    # 3. Obtener ingreso por ID
    print('3. Obteniendo ingreso por ID...')
    try:
        response = requests.get(f'{BASE_URL}/api/v1/incomes/{income_id}')
        print(f'   Status: {response.status_code}')
        if response.status_code == 200:
            income = response.json()
            print(f'   ✅ Ingreso: {income["amount_gross"]} {income["currency"]} - {income["status"]}')
        else:
            print(f'   ❌ Error: {response.text}')
    except Exception as e:
        print(f'   ❌ Error: {e}')
    
    # 4. Actualizar ingreso (PATCH)
    print('4. Actualizando ingreso...')
    update_data = {'guest_name': 'Cliente Actualizado'}
    try:
        response = requests.patch(f'{BASE_URL}/api/v1/incomes/{income_id}', 
                                json=update_data, headers=headers)
        print(f'   Status: {response.status_code}')
        if response.status_code == 200:
            print(f'   ✅ Ingreso actualizado')
        else:
            print(f'   ❌ Error: {response.text}')
    except Exception as e:
        print(f'   ❌ Error: {e}')
    
    return income_id

def test_delete_operations(apartment_id, expense_id, income_id):
    """Probar operaciones de eliminación"""
    print('\n🗑️  TESTING ELIMINACIONES')
    print('-' * 40)
    
    headers = {'X-Internal-Key': ADMIN_KEY}
    
    # 1. Eliminar gasto
    if expense_id:
        print('1. Eliminando gasto...')
        try:
            response = requests.delete(f'{BASE_URL}/api/v1/expenses/{expense_id}', 
                                     headers=headers)
            print(f'   Status: {response.status_code}')
            if response.status_code == 200:
                print(f'   ✅ Gasto eliminado')
            else:
                print(f'   ❌ Error: {response.text}')
        except Exception as e:
            print(f'   ❌ Error: {e}')
    
    # 2. Eliminar ingreso
    if income_id:
        print('2. Eliminando ingreso...')
        try:
            response = requests.delete(f'{BASE_URL}/api/v1/incomes/{income_id}', 
                                     headers=headers)
            print(f'   Status: {response.status_code}')
            if response.status_code == 200:
                print(f'   ✅ Ingreso eliminado')
            else:
                print(f'   ❌ Error: {response.text}')
        except Exception as e:
            print(f'   ❌ Error: {e}')
    
    # 3. Eliminar apartamento
    if apartment_id:
        print('3. Eliminando apartamento...')
        try:
            response = requests.delete(f'{BASE_URL}/api/v1/apartments/{apartment_id}', 
                                     headers=headers)
            print(f'   Status: {response.status_code}')
            if response.status_code == 200:
                print(f'   ✅ Apartamento eliminado')
            else:
                print(f'   ❌ Error: {response.text}')
        except Exception as e:
            print(f'   ❌ Error: {e}')

def main():
    print('🧪 TESTING APIs de GESTIÓN (CRUD)')
    print('=' * 50)
    print(f'Base URL: {BASE_URL}')
    print(f'Admin Key: {"***" + ADMIN_KEY[-4:] if len(ADMIN_KEY) > 4 else "No configurada"}')
    
    # Verificar servidor
    if not test_server_health():
        print('\n❌ No se puede continuar sin servidor')
        return
    
    # Ejecutar tests
    apartment_id = test_apartments_crud()
    expense_id = test_expenses_crud(apartment_id)
    income_id = test_incomes_crud(apartment_id)
    
    # Limpiar datos de test
    test_delete_operations(apartment_id, expense_id, income_id)
    
    print('\n✅ Tests completados')

if __name__ == '__main__':
    main()