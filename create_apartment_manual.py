#!/usr/bin/env python3
"""
Script para crear apartamentos manualmente si necesitas más
"""
import urllib.request
import urllib.error
import json

def create_apartment(code, name, owner_email="admin@sesgas.com"):
    """Crear un apartamento usando la API"""
    
    # Datos del apartamento
    apartment_data = {
        "code": code,
        "name": name,
        "owner_email": owner_email,
        "is_active": True
    }
    
    # Preparar request
    url = "https://ses-gastos.onrender.com/api/v1/apartments/"
    data = json.dumps(apartment_data).encode('utf-8')
    
    # Headers (necesitarías la ADMIN_KEY real)
    headers = {
        'Content-Type': 'application/json',
        'X-Internal-Key': 'TU_ADMIN_KEY_AQUI'  # Cambiar por la clave real
    }
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"✅ Apartamento {code} creado exitosamente:")
            print(f"   ID: {result.get('id')}")
            print(f"   Nombre: {result.get('name')}")
            return True
            
    except urllib.error.HTTPError as e:
        error_data = e.read().decode('utf-8')
        print(f"❌ Error HTTP {e.code} creando apartamento {code}:")
        print(f"   {error_data}")
        return False
        
    except Exception as e:
        print(f"❌ Error creando apartamento {code}: {e}")
        return False

def main():
    """Función principal"""
    print("🏠 Creador Manual de Apartamentos - SES.GASTOS")
    print("=" * 50)
    
    # Apartamentos por defecto
    default_apartments = [
        ("SES01", "Apartamento Centro"),
        ("SES02", "Apartamento Playa"),
        ("SES03", "Apartamento Montaña"),
        ("SES04", "Apartamento Norte"),
        ("SES05", "Apartamento Sur"),
    ]
    
    print("NOTA: Este script requiere la ADMIN_KEY correcta.")
    print("Modifica la línea 'TU_ADMIN_KEY_AQUI' con la clave real.\n")
    
    print("Apartamentos que se pueden crear:")
    for code, name in default_apartments:
        print(f"  • {code}: {name}")
    
    print(f"\n🔧 Para usar este script:")
    print(f"1. Obtén la ADMIN_KEY de las variables de entorno de Render")
    print(f"2. Modifica la línea 'TU_ADMIN_KEY_AQUI' en este script")
    print(f"3. Ejecuta: python3 create_apartment_manual.py")
    
    print(f"\n💡 Alternativamente, usa el endpoint de demo:")
    print(f"curl -X POST https://ses-gastos.onrender.com/init-demo-data")

if __name__ == "__main__":
    main()