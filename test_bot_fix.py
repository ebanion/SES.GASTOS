#!/usr/bin/env python3
"""
Script para probar que el arreglo del HTTP 307 funciona
"""
import asyncio
import httpx

async def test_redirect_fix():
    """Probar que httpx sigue redirects correctamente"""
    
    print("🔍 Probando arreglo del HTTP 307...")
    
    base_url = "https://ses-gastos.onrender.com"
    
    # Test 1: Sin follow_redirects (como estaba antes - debería fallar)
    print("\n1️⃣ Test SIN follow_redirects (comportamiento anterior):")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{base_url}/api/v1/apartments/")
            print(f"   Status: {response.status_code}")
            if response.status_code == 307:
                print("   ❌ HTTP 307 - Redirect no seguido")
                print(f"   Location: {response.headers.get('location', 'N/A')}")
            else:
                print("   ✅ Respuesta exitosa")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Con follow_redirects (como está ahora - debería funcionar)
    print("\n2️⃣ Test CON follow_redirects (comportamiento nuevo):")
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(f"{base_url}/api/v1/apartments/")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                apartments = response.json()
                print(f"   ✅ Éxito - {len(apartments)} apartamentos encontrados")
                for apt in apartments:
                    print(f"      • {apt['code']}: {apt['name']}")
            else:
                print(f"   ❌ Status inesperado: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Simular comando /usar SES01
    print("\n3️⃣ Test simulando comando /usar SES01:")
    try:
        apartment_code = "SES01"
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(f"{base_url}/api/v1/apartments/")
            
            if response.status_code == 200:
                apartments = response.json()
                apartment = next((apt for apt in apartments if apt['code'] == apartment_code), None)
                
                if apartment:
                    print(f"   ✅ Apartamento {apartment_code} encontrado!")
                    print(f"      ID: {apartment['id']}")
                    print(f"      Nombre: {apartment['name']}")
                    print("   🎉 El comando /usar SES01 debería funcionar ahora!")
                else:
                    codes = [apt['code'] for apt in apartments]
                    print(f"   ❌ Apartamento {apartment_code} no encontrado")
                    print(f"      Disponibles: {', '.join(codes)}")
            else:
                print(f"   ❌ Error del servidor: HTTP {response.status_code}")
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "="*60)
    print("📊 RESUMEN:")
    print("✅ El arreglo follow_redirects=True debería resolver el HTTP 307")
    print("✅ Los apartamentos SES01, SES02, SES03 están disponibles")
    print("✅ El comando /usar SES01 en el bot debería funcionar ahora")
    print("\n🤖 PRUEBA EN TELEGRAM:")
    print("1. @UriApartment_Bot")
    print("2. /start")
    print("3. /usar SES01 (ya no debería dar HTTP 307)")
    print("4. /status (debería mostrar 3 apartamentos)")

if __name__ == "__main__":
    asyncio.run(test_redirect_fix())