#!/usr/bin/env python3
"""
Script para verificar el estado de la aplicación en Render
"""
import requests
import time
import json
from datetime import datetime

def check_endpoint(url, timeout=10, description=""):
    """Verificar un endpoint específico"""
    try:
        print(f"🔍 Verificando {description}: {url}")
        start_time = time.time()
        
        response = requests.get(url, timeout=timeout)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ {description} - OK ({elapsed:.2f}s)")
            try:
                data = response.json()
                if isinstance(data, dict) and len(data) < 10:  # Solo mostrar si es pequeño
                    print(f"   Respuesta: {json.dumps(data, indent=2)}")
            except:
                print(f"   Respuesta: {response.text[:200]}...")
            return True, response
        else:
            print(f"❌ {description} - HTTP {response.status_code} ({elapsed:.2f}s)")
            print(f"   Error: {response.text[:200]}")
            return False, response
            
    except requests.exceptions.Timeout:
        print(f"⏰ {description} - Timeout después de {timeout}s")
        return False, None
    except requests.exceptions.ConnectionError as e:
        print(f"🔌 {description} - Error de conexión: {str(e)}")
        return False, None
    except Exception as e:
        print(f"❌ {description} - Error: {str(e)}")
        return False, None

def main():
    """Verificar estado de la aplicación"""
    print("🚀 Verificando estado de SES.GASTOS en Render...")
    print(f"⏰ Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    base_url = "https://ses-gastos.onrender.com"
    
    # Endpoints a verificar en orden de importancia
    endpoints = [
        ("/health", "Health Check"),
        ("/db-status", "Database Status"),
        ("/bot/diagnose", "Bot Diagnosis"),
        ("/bot/webhook-status", "Webhook Status"),
        ("/api/v1/dashboard/health", "Dashboard Health"),
        ("/api/v1/apartments/", "Apartments API"),
        ("/webhook/telegram/info", "Telegram Webhook Info"),
    ]
    
    results = {}
    
    for endpoint, description in endpoints:
        url = f"{base_url}{endpoint}"
        success, response = check_endpoint(url, timeout=15, description=description)
        results[endpoint] = {
            "success": success,
            "response": response.status_code if response else None
        }
        
        # Pequeña pausa entre requests
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN:")
    
    successful = sum(1 for r in results.values() if r["success"])
    total = len(results)
    
    print(f"✅ Endpoints funcionando: {successful}/{total}")
    
    if successful == 0:
        print("\n🚨 PROBLEMA CRÍTICO:")
        print("- La aplicación no responde en absoluto")
        print("- Posibles causas:")
        print("  • Despliegue aún en proceso")
        print("  • Error en el código que impide el arranque")
        print("  • Problema con las variables de entorno")
        print("  • Problema temporal de Render")
        print("\n💡 RECOMENDACIONES:")
        print("1. Esperar 2-3 minutos más")
        print("2. Verificar logs en el dashboard de Render")
        print("3. Verificar variables de entorno en Render")
        
    elif successful < total:
        print(f"\n⚠️ PROBLEMA PARCIAL:")
        print("- Algunos endpoints no funcionan")
        failed = [ep for ep, result in results.items() if not result["success"]]
        print(f"- Endpoints fallidos: {', '.join(failed)}")
        
    else:
        print("\n🎉 TODO FUNCIONANDO CORRECTAMENTE!")
        print("- La aplicación está completamente operativa")
        print("- Puedes probar el bot de Telegram ahora")
    
    print(f"\n🔗 Dashboard: {base_url}/api/v1/dashboard/")
    print(f"🤖 Bot diagnosis: {base_url}/bot/diagnose")

if __name__ == "__main__":
    main()