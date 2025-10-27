#!/usr/bin/env python3
"""
Script para crear un endpoint que arregle la tabla de ingresos en PostgreSQL
agregando las columnas faltantes de manera robusta
"""

import requests
import json

def create_migration_endpoint():
    """Crear endpoint de migración para ingresos"""
    
    migration_sql = """
    -- Migración robusta para tabla incomes
    -- Agregar columnas faltantes si no existen
    
    DO $$ 
    BEGIN
        -- guest_name
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'incomes' AND column_name = 'guest_name') THEN
            ALTER TABLE incomes ADD COLUMN guest_name VARCHAR(255);
        END IF;
        
        -- guest_email  
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'incomes' AND column_name = 'guest_email') THEN
            ALTER TABLE incomes ADD COLUMN guest_email VARCHAR(255);
        END IF;
        
        -- booking_reference
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'incomes' AND column_name = 'booking_reference') THEN
            ALTER TABLE incomes ADD COLUMN booking_reference VARCHAR(100);
        END IF;
        
        -- check_in_date
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'incomes' AND column_name = 'check_in_date') THEN
            ALTER TABLE incomes ADD COLUMN check_in_date DATE;
        END IF;
        
        -- check_out_date
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'incomes' AND column_name = 'check_out_date') THEN
            ALTER TABLE incomes ADD COLUMN check_out_date DATE;
        END IF;
        
        -- guests_count
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'incomes' AND column_name = 'guests_count') THEN
            ALTER TABLE incomes ADD COLUMN guests_count INTEGER;
        END IF;
        
        -- email_message_id
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'incomes' AND column_name = 'email_message_id') THEN
            ALTER TABLE incomes ADD COLUMN email_message_id VARCHAR(255) UNIQUE;
        END IF;
        
        -- processed_from_email
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'incomes' AND column_name = 'processed_from_email') THEN
            ALTER TABLE incomes ADD COLUMN processed_from_email BOOLEAN DEFAULT FALSE;
        END IF;
        
    END $$;
    
    -- Verificar que todas las columnas existen
    SELECT column_name, data_type, is_nullable 
    FROM information_schema.columns 
    WHERE table_name = 'incomes' 
    ORDER BY ordinal_position;
    """
    
    return migration_sql

def test_migration():
    """Probar la migración"""
    
    print("🔧 EJECUTANDO MIGRACIÓN ROBUSTA DE INGRESOS")
    print("=" * 60)
    
    base_url = "https://ses-gastos.onrender.com"
    
    # 1. Verificar conexión
    print("1️⃣ Verificando conexión...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ Servidor conectado")
        else:
            print(f"   ❌ Error de conexión: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # 2. Forzar reconexión PostgreSQL
    print("2️⃣ Asegurando conexión PostgreSQL...")
    try:
        response = requests.post(f"{base_url}/fix-postgres-now", timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"   ✅ PostgreSQL: {result.get('database', 'Conectado')}")
            else:
                print(f"   ⚠️ PostgreSQL: {result.get('message', 'Problema')}")
        else:
            print(f"   ❌ Error PostgreSQL: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 3. Ejecutar migración forzada
    print("3️⃣ Ejecutando migración...")
    try:
        response = requests.post(f"{base_url}/migrate-postgres", timeout=60)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("   ✅ Migración completada")
                for migration in result.get("migrations", []):
                    print(f"      {migration}")
            else:
                print(f"   ❌ Migración falló: {result}")
        else:
            print(f"   ❌ Error migración: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 4. Recrear tablas con SQLAlchemy
    print("4️⃣ Recreando tablas...")
    try:
        response = requests.post(f"{base_url}/create-tables-force", timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("   ✅ Tablas recreadas")
                for table in result.get("tables", []):
                    print(f"      {table}")
            else:
                print(f"   ❌ Error recreando: {result}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 5. Probar APIs de ingresos
    print("5️⃣ Probando APIs de ingresos...")
    
    # Probar listar ingresos
    try:
        response = requests.get(f"{base_url}/api/v1/incomes", timeout=10)
        if response.status_code == 200:
            incomes = response.json()
            print(f"   ✅ Listar ingresos: {len(incomes)} registros")
        elif response.status_code == 500:
            print("   ❌ Internal Server Error - Columnas aún faltantes")
        else:
            print(f"   ⚠️ Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Probar crear ingreso básico
    print("6️⃣ Probando crear ingreso...")
    try:
        response = requests.post(f"{base_url}/create-test-income", timeout=15)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("   ✅ Crear ingreso: Exitoso")
            else:
                error = result.get("error", "Error desconocido")
                if "guest_name" in error:
                    print("   ❌ Columnas aún faltantes - Necesita migración manual")
                else:
                    print(f"   ⚠️ Otro error: {error[:100]}...")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 7. Probar interfaz web
    print("7️⃣ Probando interfaz de gestión...")
    try:
        response = requests.get(f"{base_url}/admin/manage/incomes", timeout=10)
        if response.status_code == 200:
            print("   ✅ Interfaz de ingresos: Disponible")
        elif response.status_code == 500:
            print("   ❌ Interfaz: Internal Server Error")
        else:
            print(f"   ⚠️ Interfaz: Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n🎯 DIAGNÓSTICO COMPLETO:")
    print("Si las APIs de ingresos siguen fallando, el problema es que")
    print("PostgreSQL necesita una migración manual de columnas.")
    print("\nSOLUCIÓN: Acceder a la base de datos PostgreSQL directamente")
    print("y ejecutar el SQL de migración para agregar las columnas faltantes.")
    
    return True

if __name__ == "__main__":
    test_migration()