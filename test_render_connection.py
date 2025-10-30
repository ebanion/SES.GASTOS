#!/usr/bin/env python3
"""
Script de diagnóstico directo para probar conexión PostgreSQL en Render
Ejecutar desde Render Shell para diagnosticar el problema de autenticación
"""

import os
import sys

print("=" * 80)
print("🔍 DIAGNÓSTICO DE CONEXIÓN POSTGRESQL EN RENDER")
print("=" * 80)

# 1. Verificar que DATABASE_URL existe
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"\n1️⃣ DATABASE_URL configurada: {'✅ SÍ' if DATABASE_URL else '❌ NO'}")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL no está configurada en el entorno")
    print("   Ve a Render Dashboard → ses-gastos → Environment")
    sys.exit(1)

# 2. Mostrar URL (enmascarada)
import re
masked_url = re.sub(r"://([^:@]+):([^@]+)@", r"://\1:***@", DATABASE_URL)
print(f"2️⃣ URL (enmascarada): {masked_url}")

# 3. Parse manual de la URL
try:
    # Extraer componentes
    pattern = r"postgresql://([^:]+):([^@]+)@([^/:]+)(?::(\d+))?/([^?]+)(\?.*)?$"
    match = re.match(pattern, DATABASE_URL)
    
    if match:
        user = match.group(1)
        password = match.group(2)
        host = match.group(3)
        port = match.group(4) or "5432"
        database = match.group(5)
        params = match.group(6) or ""
        
        print(f"\n3️⃣ Componentes de la URL:")
        print(f"   👤 Usuario: {user}")
        print(f"   🔑 Password: {'*' * len(password)} (longitud: {len(password)} caracteres)")
        print(f"   🌍 Host: {host}")
        print(f"   🔌 Puerto: {port}")
        print(f"   🗄️  Database: {database}")
        print(f"   ⚙️  Parámetros: {params or '(ninguno)'}")
    else:
        print("⚠️ No se pudo parsear la URL con regex")
        user = None
        password = None
        host = None
        port = "5432"
        database = None
        
except Exception as e:
    print(f"❌ Error parseando URL: {e}")
    sys.exit(1)

# 4. Verificar que psycopg está instalado
print(f"\n4️⃣ Verificando psycopg...")
try:
    import psycopg
    print(f"   ✅ psycopg version: {psycopg.__version__}")
except ImportError as e:
    print(f"   ❌ psycopg no está instalado: {e}")
    sys.exit(1)

# 5. Intentar conexión DIRECTA con psycopg (sin SQLAlchemy)
print(f"\n5️⃣ Intentando conexión DIRECTA con psycopg...")
print(f"   (Esto elimina cualquier problema con SQLAlchemy)")

try:
    # Construir connection string
    conninfo = f"host={host} port={port} dbname={database} user={user} password={password} sslmode=require connect_timeout=10"
    
    print(f"   🔗 Conectando a: {host}:{port}/{database}")
    print(f"   👤 Con usuario: {user}")
    print(f"   🔒 SSL: require")
    
    conn = psycopg.connect(conninfo)
    
    print(f"   ✅ CONEXIÓN EXITOSA!")
    
    # Ejecutar query de prueba
    cursor = conn.cursor()
    cursor.execute("SELECT version()")
    version = cursor.fetchone()[0]
    
    cursor.execute("SELECT current_database()")
    current_db = cursor.fetchone()[0]
    
    cursor.execute("SELECT current_user")
    current_user = cursor.fetchone()[0]
    
    print(f"\n6️⃣ Información de la base de datos:")
    print(f"   📊 Versión: {version.split()[0]} {version.split()[1]}")
    print(f"   🗄️  Base de datos actual: {current_db}")
    print(f"   👤 Usuario actual: {current_user}")
    
    cursor.close()
    conn.close()
    
    print(f"\n" + "=" * 80)
    print(f"✅ ¡DIAGNÓSTICO EXITOSO! La conexión PostgreSQL FUNCIONA")
    print(f"=" * 80)
    print(f"\n💡 Si este script funciona pero la app no, el problema está en:")
    print(f"   1. Cómo SQLAlchemy está parseando la URL")
    print(f"   2. Los parámetros de conexión de SQLAlchemy")
    print(f"   3. El formato de DATABASE_URL para SQLAlchemy")
    
except psycopg.OperationalError as e:
    print(f"\n❌ ERROR DE CONEXIÓN:")
    print(f"   {str(e)}")
    print(f"\n🔍 Posibles causas:")
    
    error_msg = str(e).lower()
    
    if "authentication failed" in error_msg or "password" in error_msg:
        print(f"   ❌ CONTRASEÑA INCORRECTA")
        print(f"")
        print(f"   La contraseña en DATABASE_URL NO coincide con la de PostgreSQL")
        print(f"")
        print(f"   🔧 SOLUCIÓN:")
        print(f"   1. Ve a Render Dashboard → Databases → dbname_datos")
        print(f"   2. Busca 'Internal Connection String'")
        print(f"   3. Click en botón 'Copy' (NO tipes manualmente)")
        print(f"   4. Verifica que el usuario sea: {user}")
        print(f"   5. La contraseña debe tener {len(password)} caracteres")
        print(f"   6. Si no coincide, COPIA la string completa de Render")
        print(f"")
        print(f"   ⚠️ IMPORTANTE: Usa el botón COPY, no copies a mano")
        print(f"   ⚠️ La contraseña puede tener caracteres especiales")
        
    elif "connection refused" in error_msg:
        print(f"   ❌ CONEXIÓN RECHAZADA")
        print(f"   - Verifica que el host sea correcto: {host}")
        print(f"   - Verifica que el puerto sea: {port}")
        
    elif "timeout" in error_msg:
        print(f"   ❌ TIMEOUT")
        print(f"   - La base de datos no responde")
        print(f"   - Verifica que esté 'Available' en Render Dashboard")
        
    else:
        print(f"   ❌ ERROR DESCONOCIDO")
        print(f"   - Revisa la configuración en Render Dashboard")
    
    print(f"\n" + "=" * 80)
    sys.exit(1)

except Exception as e:
    print(f"\n❌ ERROR INESPERADO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
