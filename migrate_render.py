#!/usr/bin/env python3
"""
Script de migración específico para Render
Migra la estructura de PostgreSQL y configura el sistema multiusuario
"""
import os
import sys
from sqlalchemy import create_engine, text
from datetime import datetime, timezone, timedelta

def migrate_render():
    """Migrar estructura completa en Render"""
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL no configurada")
        return False
    
    print(f"🔄 Conectando a PostgreSQL...")
    
    try:
        # Crear engine con configuración específica para Render
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": 30,
                "application_name": "ses-gastos-migration"
            }
        )
        
        with engine.connect() as conn:
            print("✅ Conexión establecida")
            
            # 1. Migrar estructura de apartamentos
            print("🏠 Migrando tabla apartments...")
            
            migrations = [
                # Agregar columnas faltantes a apartments
                "ALTER TABLE apartments ADD COLUMN IF NOT EXISTS description VARCHAR(500)",
                "ALTER TABLE apartments ADD COLUMN IF NOT EXISTS address VARCHAR(500)", 
                "ALTER TABLE apartments ADD COLUMN IF NOT EXISTS max_guests INTEGER",
                "ALTER TABLE apartments ADD COLUMN IF NOT EXISTS bedrooms INTEGER",
                "ALTER TABLE apartments ADD COLUMN IF NOT EXISTS bathrooms INTEGER",
                "ALTER TABLE apartments ADD COLUMN IF NOT EXISTS account_id VARCHAR(36)",
                "ALTER TABLE apartments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE",
                
                # Agregar columnas faltantes a users
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_superadmin BOOLEAN DEFAULT FALSE",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(50)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'Europe/Madrid'",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(5) DEFAULT 'es'",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE",
                
                # Crear tabla accounts si no existe
                """CREATE TABLE IF NOT EXISTS accounts (
                    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
                    name VARCHAR(255) NOT NULL,
                    slug VARCHAR(100) UNIQUE NOT NULL,
                    description VARCHAR(500),
                    is_active BOOLEAN DEFAULT TRUE,
                    subscription_status VARCHAR(20) DEFAULT 'trial',
                    max_apartments INTEGER DEFAULT 10,
                    contact_email VARCHAR(255),
                    phone VARCHAR(50),
                    address VARCHAR(500),
                    tax_id VARCHAR(50),
                    trial_ends_at TIMESTAMP WITH TIME ZONE,
                    subscription_ends_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE
                )""",
                
                # Crear tabla account_users si no existe
                """CREATE TABLE IF NOT EXISTS account_users (
                    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
                    account_id VARCHAR(36) NOT NULL,
                    user_id VARCHAR(36) NOT NULL,
                    role VARCHAR(20) NOT NULL DEFAULT 'member',
                    is_active BOOLEAN DEFAULT TRUE,
                    invited_by VARCHAR(36),
                    invitation_accepted_at TIMESTAMP WITH TIME ZONE,
                    permissions JSON,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE,
                    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (invited_by) REFERENCES users(id) ON DELETE SET NULL
                )""",
                
                # Agregar foreign keys si no existen
                """DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints 
                        WHERE constraint_name = 'apartments_account_id_fkey' 
                        AND table_name = 'apartments'
                    ) THEN
                        ALTER TABLE apartments 
                        ADD CONSTRAINT apartments_account_id_fkey 
                        FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL;
                    END IF;
                END $$""",
            ]
            
            for migration in migrations:
                try:
                    conn.execute(text(migration))
                    print(f"  ✅ {migration[:50]}...")
                except Exception as e:
                    print(f"  ⚠️ {migration[:50]}... -> {str(e)[:100]}")
            
            conn.commit()
            print("✅ Migraciones completadas")
            
            # 2. Crear cuenta por defecto para apartamentos existentes
            print("🏢 Creando cuenta por defecto...")
            
            # Verificar si existe cuenta sistema
            result = conn.execute(text("SELECT COUNT(*) FROM accounts WHERE slug = 'sistema'")).scalar()
            
            if result == 0:
                conn.execute(text("""
                    INSERT INTO accounts (name, slug, description, max_apartments, is_active)
                    VALUES ('Sistema', 'sistema', 'Cuenta por defecto para apartamentos demo', 1000, true)
                """))
                print("  ✅ Cuenta 'Sistema' creada")
            else:
                print("  ✅ Cuenta 'Sistema' ya existe")
            
            # 3. Asignar apartamentos sin cuenta a la cuenta sistema
            print("🔗 Asignando apartamentos a cuenta sistema...")
            
            # Obtener ID de cuenta sistema
            account_id = conn.execute(text("SELECT id FROM accounts WHERE slug = 'sistema'")).scalar()
            
            # Actualizar apartamentos sin cuenta
            result = conn.execute(text("""
                UPDATE apartments 
                SET account_id = :account_id 
                WHERE account_id IS NULL
            """), {"account_id": account_id})
            
            print(f"  ✅ {result.rowcount} apartamentos asignados a cuenta sistema")
            
            conn.commit()
            
            # 4. Verificar resultado final
            print("📊 Verificando resultado...")
            
            apartments_count = conn.execute(text("SELECT COUNT(*) FROM apartments")).scalar()
            accounts_count = conn.execute(text("SELECT COUNT(*) FROM accounts")).scalar()
            users_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
            
            print(f"  📈 Apartamentos: {apartments_count}")
            print(f"  🏢 Cuentas: {accounts_count}")
            print(f"  👥 Usuarios: {users_count}")
            
            print("🎉 ¡Migración completada exitosamente!")
            return True
            
    except Exception as e:
        print(f"❌ Error en migración: {e}")
        return False

if __name__ == "__main__":
    success = migrate_render()
    sys.exit(0 if success else 1)