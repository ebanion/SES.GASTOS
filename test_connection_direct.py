#!/usr/bin/env python3
"""
Script de diagnóstico para probar conexión directa a PostgreSQL
Ejecuta esto en Render para ver exactamente qué falla
"""
import os
import sys

print("=" * 70)
print("🔍 DIAGNÓSTICO DE CONEXIÓN POSTGRESQL")
print("=" * 70)

# 1. Verificar que psycopg esté instalado
print("\n1️⃣ Verificando psycopg...")
try:
    import psycopg
    print(f"   ✅ psycopg instalado: {psycopg.__version__}")
except ImportError as e:
    print(f"   ❌ psycopg no instalado: {e}")
    sys.exit(1)

# 2. Obtener DATABASE_URL
print("\n2️⃣ Verificando DATABASE_URL...")
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("   ❌ DATABASE_URL no está configurada")
    sys.exit(1)

# Enmascarar contraseña
import re
masked = re.sub(r"://([^:@]+):([^@]+)@", r"://\1:***@", DATABASE_URL)
print(f"   ✅ DATABASE_URL encontrada")
print(f"   📋 URL: {masked}")

# Extraer partes de la URL
try:
    from urllib.parse import urlparse
    parsed = urlparse(DATABASE_URL)
    print(f"\n   📊 Detalles:")
    print(f"      Usuario: {parsed.username}")
    print(f"      Host: {parsed.hostname}")
    print(f"      Puerto: {parsed.port or 'no especificado'}")
    print(f"      Base de datos: {parsed.path.lstrip('/')}")
    print(f"      Contraseña longitud: {len(parsed.password) if parsed.password else 0} caracteres")
except Exception as e:
    print(f"   ⚠️ Error parseando URL: {e}")

# 3. Test de conexión con psycopg directamente
print("\n3️⃣ Intentando conexión con psycopg...")
print("   (Esto es lo que hace la aplicación internamente)")

try:
    # Intentar con la URL completa
    print(f"\n   📡 Conectando a: {masked}")
    conn = psycopg.connect(DATABASE_URL, connect_timeout=10)
    print("   ✅ CONEXIÓN EXITOSA!")
    
    # Ejecutar una query de prueba
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"   ✅ Query ejecutada correctamente")
    print(f"   📊 PostgreSQL version: {version.split()[1]}")
    
    cursor.execute("SELECT current_database();")
    db_name = cursor.fetchone()[0]
    print(f"   📊 Base de datos actual: {db_name}")
    
    cursor.execute("SELECT current_user;")
    current_user = cursor.fetchone()[0]
    print(f"   📊 Usuario actual: {current_user}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ ¡DIAGNÓSTICO EXITOSO! La conexión funciona correctamente.")
    print("=" * 70)
    
except psycopg.OperationalError as e:
    print(f"\n   ❌ ERROR DE CONEXIÓN (OperationalError):")
    print(f"   {str(e)}")
    print("\n   🔍 Posibles causas:")
    print("   1. Contraseña incorrecta")
    print("   2. Usuario no existe")
    print("   3. Base de datos no accesible")
    print("   4. Credenciales fueron rotadas/cambiadas")
    
    print("\n   💡 Solución:")
    print("   Ve a Render Dashboard → Databases → tu BD")
    print("   Verifica que el usuario y contraseña sean correctos")
    print("   Si no estás seguro, rota la contraseña y actualiza DATABASE_URL")
    sys.exit(1)
    
except Exception as e:
    print(f"\n   ❌ ERROR INESPERADO: {type(e).__name__}")
    print(f"   {str(e)}")
    sys.exit(1)

# 4. Test con diferentes variantes de URL
print("\n4️⃣ Probando variantes de URL...")

# Variante 1: Con sslmode
if "sslmode=" not in DATABASE_URL:
    print("\n   📡 Probando con sslmode=require...")
    url_with_ssl = DATABASE_URL
    if "?" in url_with_ssl:
        url_with_ssl += "&sslmode=require"
    else:
        url_with_ssl += "?sslmode=require"
    
    try:
        conn = psycopg.connect(url_with_ssl, connect_timeout=10)
        print("   ✅ Funciona con sslmode=require")
        conn.close()
    except Exception as e:
        print(f"   ❌ Falla con sslmode=require: {e}")

print("\n" + "=" * 70)
print("FIN DEL DIAGNÓSTICO")
print("=" * 70)
