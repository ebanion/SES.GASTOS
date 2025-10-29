#!/usr/bin/env python3
"""
Diagnóstico profundo de conexión Aiven PostgreSQL
Para ejecutar en Render Shell
"""

import os
import sys
import socket

print("=" * 80)
print("🔍 DIAGNÓSTICO PROFUNDO - AIVEN POSTGRESQL")
print("=" * 80)

# 1. Verificar DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"\n1️⃣ DATABASE_URL existe: {'✅ SÍ' if DATABASE_URL else '❌ NO'}")

if not DATABASE_URL:
    print("❌ DATABASE_URL no está configurada")
    sys.exit(1)

# 2. Parsear componentes
import re
print(f"\n2️⃣ Parseando URL...")

try:
    pattern = r"^postgres(?:ql)?://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)(\?.*)?$"
    match = re.match(pattern, DATABASE_URL)
    
    if match:
        user = match.group(1)
        password = match.group(2)
        host = match.group(3)
        port = int(match.group(4))
        database = match.group(5)
        params = match.group(6) or ""
        
        print(f"   👤 Usuario: {user}")
        print(f"   🔑 Password: {'*' * len(password)} ({len(password)} chars)")
        print(f"   🌍 Host: {host}")
        print(f"   🔌 Puerto: {port}")
        print(f"   🗄️  Database: {database}")
        print(f"   ⚙️  Params: {params}")
    else:
        print(f"   ❌ No se pudo parsear la URL")
        print(f"   URL (masked): {DATABASE_URL[:30]}...{DATABASE_URL[-30:]}")
        sys.exit(1)
        
except Exception as e:
    print(f"   ❌ Error parseando: {e}")
    sys.exit(1)

# 3. Test de conectividad de red (socket)
print(f"\n3️⃣ Verificando conectividad de red al host...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    result = sock.connect_ex((host, port))
    sock.close()
    
    if result == 0:
        print(f"   ✅ Puerto {port} ACCESIBLE en {host}")
    else:
        print(f"   ❌ Puerto {port} NO ACCESIBLE en {host}")
        print(f"   ⚠️ PROBLEMA: Firewall o red bloqueando conexión")
        print(f"\n   🔧 SOLUCIÓN:")
        print(f"   1. Ve a Aiven Dashboard → Tu servicio → 'Networking'")
        print(f"   2. Verifica 'Allowed IP addresses'")
        print(f"   3. Debe permitir 'Anywhere (0.0.0.0/0)' o añade IPs de Render")
        sys.exit(1)
        
except Exception as e:
    print(f"   ❌ Error verificando red: {e}")
    sys.exit(1)

# 4. Verificar psycopg
print(f"\n4️⃣ Verificando psycopg...")
try:
    import psycopg
    print(f"   ✅ psycopg version: {psycopg.__version__}")
except ImportError as e:
    print(f"   ❌ psycopg no disponible: {e}")
    sys.exit(1)

# 5. Intentar conexión con detalles extendidos
print(f"\n5️⃣ Intentando conexión PostgreSQL con diagnóstico extendido...")

try:
    # Construir conninfo con opciones extendidas
    conninfo = f"host={host} port={port} dbname={database} user={user} password={password} sslmode=require connect_timeout=10"
    
    print(f"   🔗 Conectando...")
    print(f"   📍 Target: {host}:{port}")
    print(f"   👤 User: {user}")
    print(f"   🗄️  DB: {database}")
    
    conn = psycopg.connect(conninfo)
    
    print(f"\n   ✅ ¡CONEXIÓN EXITOSA!")
    
    cursor = conn.cursor()
    
    # Info de versión
    cursor.execute("SELECT version()")
    version = cursor.fetchone()[0]
    print(f"\n6️⃣ Información de la base de datos:")
    print(f"   📊 PostgreSQL: {version.split()[1]}")
    
    # Info de usuario actual
    cursor.execute("SELECT current_user, current_database()")
    current_user, current_db = cursor.fetchone()
    print(f"   👤 Usuario conectado: {current_user}")
    print(f"   🗄️  Base de datos: {current_db}")
    
    # Info de conexión SSL
    cursor.execute("SELECT ssl_is_used()")
    ssl_used = cursor.fetchone()[0]
    print(f"   🔒 SSL activo: {'✅ SÍ' if ssl_used else '❌ NO'}")
    
    cursor.close()
    conn.close()
    
    print(f"\n" + "=" * 80)
    print(f"✅ DIAGNÓSTICO EXITOSO - PostgreSQL FUNCIONA CORRECTAMENTE")
    print(f"=" * 80)
    print(f"\n💡 Si este script funciona pero la app no:")
    print(f"   - El problema está en cómo la app procesa DATABASE_URL")
    print(f"   - Revisa los logs de la app para ver qué URL exacta usa")
    
except psycopg.OperationalError as e:
    error_msg = str(e)
    print(f"\n   ❌ ERROR DE CONEXIÓN POSTGRESQL:")
    print(f"   {error_msg}")
    
    print(f"\n🔍 ANÁLISIS DEL ERROR:")
    
    if "authentication failed" in error_msg.lower() or "password" in error_msg.lower():
        print(f"\n   🚨 ERROR DE AUTENTICACIÓN DETECTADO")
        print(f"\n   Posibles causas (en orden de probabilidad):")
        print(f"\n   1️⃣ FIREWALL/ACL EN AIVEN")
        print(f"      - Aiven puede estar bloqueando la IP de Render")
        print(f"      - Ve a Aiven Dashboard → Networking → Allowed IP addresses")
        print(f"      - Debe estar en '0.0.0.0/0' (Anywhere) o incluir IPs de Render")
        print(f"\n   2️⃣ USUARIO NO TIENE PERMISOS")
        print(f"      - Ve a Aiven Dashboard → Users")
        print(f"      - Verifica que 'avnadmin' tenga rol de 'Admin'")
        print(f"      - Intenta crear un nuevo usuario con permisos completos")
        print(f"\n   3️⃣ MÉTODO DE AUTENTICACIÓN")
        print(f"      - Aiven puede usar SCRAM-SHA-256 que requiere config especial")
        print(f"      - Intenta añadir: ?sslmode=require&gssencmode=disable")
        print(f"\n   4️⃣ CERTIFICADO SSL")
        print(f"      - Aiven puede requerir CA certificate específico")
        print(f"      - Descarga el CA cert de Aiven y úsalo en la conexión")
        
    elif "connection refused" in error_msg.lower():
        print(f"   ❌ CONEXIÓN RECHAZADA")
        print(f"      - El servidor rechazó la conexión")
        print(f"      - Verifica que el servicio esté 'Running' en Aiven")
        
    elif "timeout" in error_msg.lower():
        print(f"   ❌ TIMEOUT")
        print(f"      - No se pudo conectar en 10 segundos")
        print(f"      - Verifica firewall/networking en Aiven")
        
    else:
        print(f"   ❌ ERROR DESCONOCIDO")
    
    print(f"\n" + "=" * 80)
    sys.exit(1)

except Exception as e:
    print(f"\n   ❌ ERROR INESPERADO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
