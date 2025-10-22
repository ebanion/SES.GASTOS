#!/usr/bin/env python3
"""
Script para probar el bot localmente con la configuración de producción
"""
import os
import sys
sys.path.append('.')

def test_bot_locally():
    print("🤖 Probando bot de Telegram localmente...")
    
    # Verificar variables de entorno
    required_vars = {
        "TELEGRAM_TOKEN": os.getenv("TELEGRAM_TOKEN"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "API_BASE_URL": os.getenv("API_BASE_URL", "https://ses-gastos.onrender.com"),
        "INTERNAL_KEY": os.getenv("INTERNAL_KEY") or os.getenv("ADMIN_KEY")
    }
    
    print("\n📋 Variables de entorno:")
    for var, value in required_vars.items():
        status = "✅" if value else "❌"
        masked_value = f"***{value[-4:]}" if value and len(value) > 4 else "No configurada"
        print(f"   {status} {var}: {masked_value}")
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        print(f"\n❌ Variables faltantes: {', '.join(missing_vars)}")
        print("Configúralas en tu entorno antes de ejecutar el bot.")
        return False
    
    # Probar conexión con Telegram
    print("\n🔗 Probando conexión con Telegram API...")
    try:
        import requests
        token = required_vars["TELEGRAM_TOKEN"]
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()["result"]
            print(f"   ✅ Bot conectado: @{bot_info['username']} ({bot_info['first_name']})")
        else:
            print(f"   ❌ Error de conexión: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Probar conexión con API
    print("\n🌐 Probando conexión con API...")
    try:
        api_url = required_vars["API_BASE_URL"]
        response = requests.get(f"{api_url}/health", timeout=10)
        if response.status_code == 200:
            print(f"   ✅ API conectada: {api_url}")
        else:
            print(f"   ❌ API no responde: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error API: {e}")
        return False
    
    # Verificar apartamentos
    print("\n🏠 Verificando apartamentos...")
    try:
        response = requests.get(f"{api_url}/api/v1/apartments/", timeout=10)
        if response.status_code == 200:
            apartments = response.json()
            print(f"   ✅ Apartamentos disponibles: {len(apartments)}")
            for apt in apartments[:3]:
                print(f"      - {apt['code']}: {apt.get('name', 'Sin nombre')}")
        else:
            print(f"   ⚠️ No se pudieron obtener apartamentos: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error obteniendo apartamentos: {e}")
    
    print("\n🚀 Todo listo para ejecutar el bot!")
    print("\n📱 Para probar:")
    print("1. python app/bot/Telegram_expense_bot.py")
    print("2. En Telegram: /start")
    print("3. /usar SES01")
    print("4. Enviar foto de factura")
    
    return True

if __name__ == "__main__":
    success = test_bot_locally()
    if success:
        print("\n🎉 ¡Configuración correcta! El bot debería funcionar.")
    else:
        print("\n❌ Hay problemas de configuración que resolver.")