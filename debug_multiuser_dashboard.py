#!/usr/bin/env python3
"""
Script para debuggear el problema del dashboard multiusuario
"""
import requests
import json

BASE_URL = "https://ses-gastos.onrender.com"

def test_login_and_apartments():
    """Test completo del flujo de login y apartamentos"""
    
    print("🔍 Testing Multiuser Dashboard Issue")
    print("=" * 50)
    
    # 1. Test login con cuenta demo
    print("\n1. Testing login...")
    login_data = {
        "email": "demo@example.com",
        "password": "123456"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        print(f"Login Status: {response.status_code}")
        
        if response.status_code == 200:
            login_result = response.json()
            print(f"✅ Login successful")
            print(f"User: {login_result['user']['email']}")
            print(f"Accounts: {len(login_result['accounts'])}")
            
            token = login_result['access_token']
            default_account_id = login_result.get('default_account_id')
            
            if login_result['accounts']:
                account = login_result['accounts'][0]
                print(f"Account ID: {account['id']}")
                print(f"Account Name: {account['name']}")
                
                # 2. Test apartments endpoint
                print(f"\n2. Testing apartments endpoint...")
                headers = {
                    'Authorization': f'Bearer {token}',
                    'X-Account-ID': account['id']
                }
                
                apartments_response = requests.get(f"{BASE_URL}/api/v1/apartments/", headers=headers)
                print(f"Apartments Status: {apartments_response.status_code}")
                
                if apartments_response.status_code == 200:
                    apartments = apartments_response.json()
                    print(f"✅ Apartments loaded: {len(apartments)}")
                    for apt in apartments:
                        print(f"  - {apt['code']}: {apt['name']} (Account: {apt.get('account_id', 'N/A')})")
                else:
                    print(f"❌ Apartments failed: {apartments_response.text}")
                
                # 3. Test legacy apartments endpoint
                print(f"\n3. Testing legacy apartments endpoint...")
                legacy_response = requests.get(f"{BASE_URL}/api/v1/apartments", headers=headers)
                print(f"Legacy Status: {legacy_response.status_code}")
                
                if legacy_response.status_code == 200:
                    legacy_apartments = legacy_response.json()
                    print(f"Legacy apartments: {len(legacy_apartments)}")
                    for apt in legacy_apartments:
                        print(f"  - {apt['code']}: {apt['name']} (Account: {apt.get('account_id', 'N/A')})")
                
            else:
                print("❌ No accounts found for user")
        else:
            print(f"❌ Login failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_system_status():
    """Test system status endpoints"""
    print("\n4. Testing system status...")
    
    try:
        # Test migration status
        migration_response = requests.get(f"{BASE_URL}/migrate/status")
        print(f"Migration Status: {migration_response.status_code}")
        
        if migration_response.status_code == 200:
            migration_data = migration_response.json()
            print(f"System Ready: {migration_data.get('system_ready', False)}")
            print(f"Accounts: {migration_data.get('accounts', {}).get('total', 0)}")
            print(f"Users: {migration_data.get('users', {}).get('total', 0)}")
            print(f"Apartments: {migration_data.get('apartments', {}).get('total', 0)}")
        
        # Test dashboard health
        health_response = requests.get(f"{BASE_URL}/api/v1/dashboard/health")
        print(f"Dashboard Health: {health_response.status_code}")
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"Database: {health_data.get('database', 'unknown')}")
            print(f"Tables: {health_data.get('tables', {})}")
            
    except Exception as e:
        print(f"❌ System status error: {e}")

if __name__ == "__main__":
    test_login_and_apartments()
    test_system_status()
    
    print("\n" + "=" * 50)
    print("🔧 DIAGNOSIS:")
    print("If you see SES01, SES02, SES03 in your dashboard but not your own apartments,")
    print("the issue is likely:")
    print("1. Dashboard is calling wrong endpoint (legacy vs multiuser)")
    print("2. X-Account-ID header not being sent correctly")
    print("3. Account isolation not working properly")
    print("4. Your apartments were created in wrong account")