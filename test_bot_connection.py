#!/usr/bin/env python3
"""
Script para probar la conexión con el bot de Telegram sin dependencias externas
"""
import urllib.request
import urllib.error
import json
import time
import socket
from datetime import datetime

def test_connection(url, timeout=15, description=""):
    """Probar conexión a un endpoint"""
    print(f"🔍 Probando {description}: {url}")
    
    try:
        start_time = time.time()
        
        # Configurar timeout
        socket.setdefaulttimeout(timeout)
        
        # Hacer request
        with urllib.request.urlopen(url, timeout=timeout) as response:
            elapsed = time.time() - start_time
            status_code = response.getcode()
            data = response.read().decode('utf-8')
            
            if status_code == 200:
                print(f"✅ {description} - OK ({elapsed:.2f}s)")
                try:
                    json_data = json.loads(data)
                    if isinstance(json_data, dict) and len(str(json_data)) < 500:
                        print(f"   📄 Respuesta: {json.dumps(json_data, indent=2, ensure_ascii=False)}")
                    else:
                        print(f"   📄 Respuesta: {data[:200]}...")
                except:
                    print(f"   📄 Respuesta: {data[:200]}...")
                return True, status_code, data
            else:
                print(f"❌ {description} - HTTP {status_code} ({elapsed:.2f}s)")
                return False, status_code, data
                
    except urllib.error.URLError as e:
        if hasattr(e, 'reason'):
            print(f"🔌 {description} - Error de conexión: {e.reason}")
        else:
            print(f"🔌 {description} - Error de URL: {e}")
        return False, None, None
        
    except socket.timeout:
        print(f"⏰ {description} - Timeout después de {timeout}s")
        return False, None, None
        
    except Exception as e:
        print(f"❌ {description} - Error: {str(e)}")
        return False, None, None

def main():
    """Función principal de diagnóstico"""
    print("🚀 Diagnóstico de Conectividad - SES.GASTOS")
    print(f"⏰ Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    base_url = "https://ses-gastos.onrender.com"
    
    # Tests básicos primero
    basic_tests = [
        ("/health", "Health Check Básico"),
        ("/db-status", "Estado Base de Datos"),
    ]
    
    print("🔧 TESTS BÁSICOS:")
    basic_success = 0
    
    for endpoint, desc in basic_tests:
        url = f"{base_url}{endpoint}"
        success, status, data = test_connection(url, timeout=20, description=desc)
        if success:
            basic_success += 1
        time.sleep(1)
    
    if basic_success == 0:
        print("\n🚨 PROBLEMA CRÍTICO DE CONECTIVIDAD:")
        print("- No se puede conectar a la aplicación")
        print("- Posibles causas:")
        print("  • Problema de red local")
        print("  • Firewall bloqueando conexiones")
        print("  • DNS no resuelve correctamente")
        print("  • Proxy/VPN interfiriendo")
        print("\n💡 SOLUCIONES:")
        print("1. Probar desde otra red (móvil, etc.)")
        print("2. Verificar configuración de proxy/VPN")
        print("3. Probar directamente en navegador:")
        print(f"   {base_url}/health")
        return
    
    print(f"\n✅ Tests básicos: {basic_success}/{len(basic_tests)}")
    
    # Tests del bot
    print("\n🤖 TESTS DEL BOT:")
    bot_tests = [
        ("/bot/diagnose", "Diagnóstico del Bot"),
        ("/bot/webhook-status", "Estado del Webhook"),
    ]
    
    bot_success = 0
    bot_info = None
    
    for endpoint, desc in bot_tests:
        url = f"{base_url}{endpoint}"
        success, status, data = test_connection(url, timeout=25, description=desc)
        if success:
            bot_success += 1
            if endpoint == "/bot/diagnose" and data:
                try:
                    bot_info = json.loads(data)
                except:
                    pass
        time.sleep(1)
    
    print(f"\n✅ Tests del bot: {bot_success}/{len(bot_tests)}")
    
    # Análisis del bot
    if bot_info:
        print("\n📊 ANÁLISIS DEL BOT:")
        env = bot_info.get("environment", {})
        init = bot_info.get("initialization", {})
        webhook = bot_info.get("webhook", {})
        
        print(f"🔑 Token Telegram: {env.get('telegram_token', '❌')}")
        print(f"🧠 OpenAI Key: {env.get('openai_key', '❌')}")
        print(f"🔐 Admin Key: {env.get('admin_key', '❌')}")
        print(f"🤖 Inicialización: {init.get('status', '❌')}")
        print(f"🔗 Webhook: {webhook.get('status', '❌')}")
        
        if init.get("bot_info"):
            bot_data = init["bot_info"]
            print(f"📱 Bot Username: @{bot_data.get('username', 'N/A')}")
            print(f"🆔 Bot ID: {bot_data.get('id', 'N/A')}")
        
        recommendations = bot_info.get("recommendations", [])
        if recommendations:
            print(f"\n⚠️ Recomendaciones:")
            for rec in recommendations:
                print(f"   • {rec}")
        
        overall = bot_info.get("overall_status", "")
        print(f"\n🎯 Estado General: {overall}")
    
    # Instrucciones finales
    print("\n" + "=" * 60)
    print("📱 CÓMO PROBAR EL BOT:")
    
    if bot_info and bot_info.get("initialization", {}).get("bot_info"):
        username = bot_info["initialization"]["bot_info"].get("username")
        print(f"1. Abrir Telegram")
        print(f"2. Buscar: @{username}")
        print(f"3. Enviar: /start")
        print(f"4. Enviar: /usar SES01")
        print(f"5. Enviar una foto")
        print(f"6. Seguir instrucciones para datos manuales")
    else:
        print("❌ No se pudo obtener información del bot")
    
    print(f"\n🌐 Dashboard: {base_url}/api/v1/dashboard/")
    
    if basic_success == len(basic_tests) and bot_success == len(bot_tests):
        print("\n🎉 ¡TODO FUNCIONANDO! El bot debería responder en Telegram.")
    else:
        print(f"\n⚠️ Algunos tests fallaron. Revisa la conectividad.")

if __name__ == "__main__":
    main()