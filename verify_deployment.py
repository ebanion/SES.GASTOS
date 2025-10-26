#!/usr/bin/env python3
"""
Script para verificar el despliegue en Render
"""
import requests
import json
import sys
from datetime import datetime

def verify_deployment(base_url):
    """Verificar que el despliegue esté funcionando correctamente"""
    print(f"🔍 VERIFICANDO DESPLIEGUE EN: {base_url}")
    print("=" * 60)
    
    results = []
    
    # Lista de endpoints a verificar
    endpoints = [
        {
            "name": "Health Check",
            "url": f"{base_url}/health",
            "method": "GET",
            "expected_status": 200,
            "expected_content": {"ok": True}
        },
        {
            "name": "Database Status",
            "url": f"{base_url}/db-status", 
            "method": "GET",
            "expected_status": 200,
            "expected_keys": ["database", "status"]
        },
        {
            "name": "Dashboard Health",
            "url": f"{base_url}/api/v1/dashboard/health",
            "method": "GET", 
            "expected_status": 200,
            "expected_keys": ["status", "database"]
        },
        {
            "name": "Apartments List",
            "url": f"{base_url}/api/v1/apartments/",
            "method": "GET",
            "expected_status": 200,
            "expected_type": list
        },
        {
            "name": "Bot Status",
            "url": f"{base_url}/bot/status",
            "method": "GET",
            "expected_status": 200,
            "optional": True  # Puede fallar si no hay TELEGRAM_TOKEN
        },
        {
            "name": "Dashboard Web",
            "url": f"{base_url}/api/v1/dashboard/",
            "method": "GET",
            "expected_status": 200,
            "content_type": "text/html"
        }
    ]
    
    for i, endpoint in enumerate(endpoints, 1):
        print(f"\n{i}. Verificando {endpoint['name']}...")
        
        try:
            # Hacer request
            response = requests.get(endpoint["url"], timeout=30)
            
            # Verificar status code
            if response.status_code == endpoint["expected_status"]:
                print(f"   ✅ Status: {response.status_code}")
                
                # Verificar contenido si es JSON
                if endpoint.get("content_type") != "text/html":
                    try:
                        data = response.json()
                        
                        # Verificar contenido específico
                        if "expected_content" in endpoint:
                            if data == endpoint["expected_content"]:
                                print(f"   ✅ Contenido correcto")
                                results.append({"endpoint": endpoint["name"], "status": "✅ OK"})
                            else:
                                print(f"   ⚠️ Contenido inesperado: {data}")
                                results.append({"endpoint": endpoint["name"], "status": "⚠️ Contenido diferente"})
                        
                        # Verificar claves esperadas
                        elif "expected_keys" in endpoint:
                            missing_keys = [key for key in endpoint["expected_keys"] if key not in data]
                            if not missing_keys:
                                print(f"   ✅ Claves requeridas presentes")
                                results.append({"endpoint": endpoint["name"], "status": "✅ OK"})
                            else:
                                print(f"   ⚠️ Claves faltantes: {missing_keys}")
                                results.append({"endpoint": endpoint["name"], "status": f"⚠️ Claves faltantes: {missing_keys}"})
                        
                        # Verificar tipo esperado
                        elif "expected_type" in endpoint:
                            if isinstance(data, endpoint["expected_type"]):
                                print(f"   ✅ Tipo correcto: {type(data).__name__}")
                                print(f"   ℹ️ Elementos: {len(data) if hasattr(data, '__len__') else 'N/A'}")
                                results.append({"endpoint": endpoint["name"], "status": "✅ OK"})
                            else:
                                print(f"   ⚠️ Tipo inesperado: {type(data).__name__}")
                                results.append({"endpoint": endpoint["name"], "status": f"⚠️ Tipo inesperado"})
                        
                        else:
                            print(f"   ✅ Respuesta JSON válida")
                            results.append({"endpoint": endpoint["name"], "status": "✅ OK"})
                            
                    except json.JSONDecodeError:
                        print(f"   ⚠️ Respuesta no es JSON válido")
                        results.append({"endpoint": endpoint["name"], "status": "⚠️ No JSON"})
                
                else:
                    # Para HTML, solo verificar que no esté vacío
                    if len(response.text) > 100:
                        print(f"   ✅ HTML válido ({len(response.text)} caracteres)")
                        results.append({"endpoint": endpoint["name"], "status": "✅ OK"})
                    else:
                        print(f"   ⚠️ HTML muy corto ({len(response.text)} caracteres)")
                        results.append({"endpoint": endpoint["name"], "status": "⚠️ HTML corto"})
            
            else:
                if endpoint.get("optional") and response.status_code in [500, 403]:
                    print(f"   ⚠️ Status: {response.status_code} (opcional, puede estar sin configurar)")
                    results.append({"endpoint": endpoint["name"], "status": "⚠️ Opcional sin configurar"})
                else:
                    print(f"   ❌ Status: {response.status_code} (esperado: {endpoint['expected_status']})")
                    print(f"   ❌ Error: {response.text[:200]}...")
                    results.append({"endpoint": endpoint["name"], "status": f"❌ Error {response.status_code}"})
        
        except requests.exceptions.Timeout:
            print(f"   ❌ Timeout (>30s)")
            results.append({"endpoint": endpoint["name"], "status": "❌ Timeout"})
        
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Error de conexión")
            results.append({"endpoint": endpoint["name"], "status": "❌ Sin conexión"})
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({"endpoint": endpoint["name"], "status": f"❌ Error: {str(e)[:50]}"})
    
    # Resumen
    print(f"\n📊 RESUMEN DE VERIFICACIÓN:")
    print("=" * 40)
    
    ok_count = sum(1 for r in results if r["status"].startswith("✅"))
    warning_count = sum(1 for r in results if r["status"].startswith("⚠️"))
    error_count = sum(1 for r in results if r["status"].startswith("❌"))
    
    for result in results:
        print(f"   {result['status']} {result['endpoint']}")
    
    print(f"\n📈 ESTADÍSTICAS:")
    print(f"   ✅ Exitosos: {ok_count}")
    print(f"   ⚠️ Advertencias: {warning_count}")
    print(f"   ❌ Errores: {error_count}")
    print(f"   📊 Total: {len(results)}")
    
    # Determinar estado general
    if error_count == 0:
        if warning_count == 0:
            print(f"\n🎉 DESPLIEGUE PERFECTO - Todo funcionando correctamente")
            return True
        else:
            print(f"\n✅ DESPLIEGUE EXITOSO - Funcional con advertencias menores")
            return True
    else:
        if ok_count > error_count:
            print(f"\n⚠️ DESPLIEGUE PARCIAL - Algunos servicios no funcionan")
            return False
        else:
            print(f"\n❌ DESPLIEGUE FALLIDO - Errores críticos")
            return False

def main():
    """Función principal"""
    if len(sys.argv) != 2:
        print("Uso: python3 verify_deployment.py <URL_BASE>")
        print("Ejemplo: python3 verify_deployment.py https://tu-app.onrender.com")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    
    print(f"🚀 VERIFICACIÓN DE DESPLIEGUE - SES.GASTOS")
    print(f"🌐 URL: {base_url}")
    print(f"⏰ Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = verify_deployment(base_url)
    
    if success:
        print(f"\n🎯 PRÓXIMOS PASOS:")
        print(f"   1. Acceder al dashboard: {base_url}/api/v1/dashboard/")
        print(f"   2. Configurar bot Telegram (si aplica): POST {base_url}/bot/setup-webhook")
        print(f"   3. Probar funcionalidades desde el dashboard")
        print(f"   4. Monitorear logs en Render Dashboard")
    else:
        print(f"\n🔧 ACCIONES RECOMENDADAS:")
        print(f"   1. Revisar logs en Render Dashboard")
        print(f"   2. Verificar variables de entorno")
        print(f"   3. Comprobar estado de PostgreSQL")
        print(f"   4. Ejecutar redeploy si es necesario")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()