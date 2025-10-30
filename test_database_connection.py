#!/usr/bin/env python3
"""
Test de validación de DATABASE_URL
Ejecutar antes de arrancar la app para detectar problemas
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

def test_database_url():
    """Test que valida DATABASE_URL antes de arrancar app"""
    
    print("=" * 80)
    print("🧪 TEST DE VALIDACIÓN DATABASE_URL")
    print("=" * 80)
    
    # Test 1: Existe
    print("\n1️⃣ Verificando que DATABASE_URL existe...")
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        print("❌ FAIL: DATABASE_URL no configurada")
        sys.exit(1)
    
    print(f"✅ PASS: DATABASE_URL configurada")
    print(f"   Length: {len(DATABASE_URL)} chars")
    
    # Test 2: No tiene whitespace
    print("\n2️⃣ Verificando whitespace...")
    stripped = DATABASE_URL.strip()
    
    if DATABASE_URL != stripped:
        print(f"❌ FAIL: DATABASE_URL tiene whitespace")
        print(f"   Original: {repr(DATABASE_URL[-50:])}")
        print(f"   Stripped: {repr(stripped[-50:])}")
        sys.exit(1)
    
    print(f"✅ PASS: Sin whitespace")
    
    # Test 3: Driver correcto
    print("\n3️⃣ Verificando driver...")
    
    try:
        url = make_url(DATABASE_URL)
    except Exception as e:
        print(f"❌ FAIL: No se pudo parsear DATABASE_URL: {e}")
        print(f"   Repr: {repr(DATABASE_URL[:100])}")
        sys.exit(1)
    
    if "postgresql" in url.drivername or "postgres" in url.drivername:
        # Normalizar a postgresql+psycopg
        if url.drivername == "postgres":
            url = url.set(drivername="postgresql+psycopg")
        elif url.drivername == "postgresql":
            url = url.set(drivername="postgresql+psycopg")
        
        expected_driver = "postgresql+psycopg"
        actual_driver = url.drivername
        
        if actual_driver != expected_driver:
            print(f"⚠️ WARN: Driver no óptimo: {actual_driver}")
            print(f"   Recomendado: {expected_driver}")
        else:
            print(f"✅ PASS: Driver correcto: {actual_driver}")
    
    # Test 4: Componentes válidos
    print("\n4️⃣ Verificando componentes...")
    print(f"   Host: {url.host}")
    print(f"   Port: {url.port}")
    print(f"   Database: {url.database}")
    print(f"   Username: {url.username}")
    print(f"   Password length: {len(url.password) if url.password else 0} chars")
    
    if not url.host:
        print(f"❌ FAIL: Host vacío")
        sys.exit(1)
    
    if not url.database:
        print(f"❌ FAIL: Database vacío")
        sys.exit(1)
    
    if not url.username:
        print(f"❌ FAIL: Username vacío")
        sys.exit(1)
    
    if not url.password:
        print(f"❌ FAIL: Password vacía")
        sys.exit(1)
    
    print(f"✅ PASS: Todos los componentes presentes")
    
    # Test 5: SSL configurado
    print("\n5️⃣ Verificando SSL...")
    sslmode = url.query.get("sslmode")
    
    if not sslmode:
        print(f"⚠️ WARN: sslmode no configurado (recomendado: require)")
    else:
        print(f"✅ PASS: sslmode={sslmode}")
    
    # Test 6: Conectividad básica
    print("\n6️⃣ Probando conectividad...")
    
    try:
        # Normalizar URL para SQLAlchemy
        if url.drivername in ["postgres", "postgresql"]:
            url = url.set(drivername="postgresql+psycopg")
        
        # Asegurar sslmode
        if not url.query.get("sslmode"):
            query_params = dict(url.query)
            query_params["sslmode"] = "require"
            url = url.set(query=query_params)
        
        test_url = str(url)
        
        engine = create_engine(
            test_url, 
            pool_pre_ping=True, 
            connect_args={"connect_timeout": 10}
        )
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            if result != 1:
                print(f"❌ FAIL: SELECT 1 devolvió {result}")
                sys.exit(1)
            
            # Info adicional
            version = conn.execute(text("SELECT version()")).scalar()
            db_name = conn.execute(text("SELECT current_database()")).scalar()
            
            print(f"✅ PASS: Conexión exitosa")
            print(f"   PostgreSQL version: {version.split()[1]}")
            print(f"   Database: {db_name}")
        
        engine.dispose()
        
    except Exception as e:
        print(f"❌ FAIL: No se pudo conectar: {e}")
        
        # Diagnosticar tipo de error
        error_msg = str(e).lower()
        
        if "authentication failed" in error_msg or "password" in error_msg:
            print(f"\n🔍 Diagnóstico:")
            print(f"   - Error de AUTENTICACIÓN")
            print(f"   - Verifica password en DATABASE_URL")
            print(f"   - Verifica firewall/ACL en proveedor")
            print(f"   - Password length actual: {len(url.password)} chars")
        elif "timeout" in error_msg:
            print(f"\n🔍 Diagnóstico:")
            print(f"   - TIMEOUT de conexión")
            print(f"   - Verifica que el servidor esté corriendo")
            print(f"   - Verifica firewall/networking")
        elif "connection refused" in error_msg:
            print(f"\n🔍 Diagnóstico:")
            print(f"   - Conexión RECHAZADA")
            print(f"   - Verifica host y puerto")
            print(f"   - Verifica que el servicio esté activo")
        
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("✅ TODOS LOS TESTS PASARON")
    print("=" * 80)
    print("\n💡 DATABASE_URL está lista para usarse")
    
if __name__ == "__main__":
    test_database_url()
