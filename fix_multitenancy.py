#!/usr/bin/env python3
"""
Script para diagnosticar y arreglar problemas de multitenancy
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal
from app.models import Apartment, Account, User, AccountUser
from sqlalchemy import and_

def diagnose_multitenancy():
    """Diagnosticar problemas de multitenancy"""
    
    db = SessionLocal()
    try:
        print("🔍 DIAGNÓSTICO DE MULTITENANCY")
        print("=" * 50)
        
        # 1. Verificar estructura de cuentas
        print("\n1. 📊 ESTRUCTURA DE CUENTAS:")
        accounts = db.query(Account).all()
        print(f"   Total cuentas: {len(accounts)}")
        
        for account in accounts:
            users_count = db.query(AccountUser).filter(AccountUser.account_id == account.id).count()
            apartments_count = db.query(Apartment).filter(Apartment.account_id == account.id).count()
            
            print(f"   - {account.name} (@{account.slug})")
            print(f"     ID: {account.id}")
            print(f"     Usuarios: {users_count}")
            print(f"     Apartamentos: {apartments_count}")
            print(f"     Activa: {account.is_active}")
            
            # Mostrar apartamentos de esta cuenta
            apartments = db.query(Apartment).filter(Apartment.account_id == account.id).all()
            for apt in apartments:
                print(f"       🏠 {apt.code}: {apt.name} (Owner: {apt.owner_email})")
        
        # 2. Verificar apartamentos sin cuenta (legacy)
        print("\n2. 🏠 APARTAMENTOS LEGACY (SIN CUENTA):")
        legacy_apartments = db.query(Apartment).filter(Apartment.account_id == None).all()
        print(f"   Total legacy: {len(legacy_apartments)}")
        
        for apt in legacy_apartments:
            print(f"   - {apt.code}: {apt.name} (Owner: {apt.owner_email})")
        
        # 3. Verificar usuarios y sus membresías
        print("\n3. 👥 USUARIOS Y MEMBRESÍAS:")
        users = db.query(User).all()
        print(f"   Total usuarios: {len(users)}")
        
        for user in users:
            memberships = db.query(AccountUser).filter(AccountUser.user_id == user.id).all()
            print(f"   - {user.email} ({'Superadmin' if user.is_superadmin else 'Usuario'})")
            print(f"     ID: {user.id}")
            print(f"     Membresías: {len(memberships)}")
            
            for membership in memberships:
                account = db.query(Account).filter(Account.id == membership.account_id).first()
                print(f"       → {account.name if account else 'Cuenta eliminada'} ({membership.role})")
        
        # 4. Detectar problemas
        print("\n4. 🚨 PROBLEMAS DETECTADOS:")
        problems = []
        
        if legacy_apartments:
            problems.append(f"❌ {len(legacy_apartments)} apartamentos sin cuenta (legacy)")
        
        # Verificar apartamentos con owner_email que no coincide con ninguna cuenta
        for apt in db.query(Apartment).all():
            if apt.owner_email and apt.account_id:
                account = db.query(Account).filter(Account.id == apt.account_id).first()
                if account and account.contact_email != apt.owner_email:
                    problems.append(f"⚠️ Apartamento {apt.code}: email owner ({apt.owner_email}) ≠ email cuenta ({account.contact_email})")
        
        # Verificar cuentas sin usuarios
        for account in accounts:
            users_count = db.query(AccountUser).filter(AccountUser.account_id == account.id).count()
            if users_count == 0:
                problems.append(f"⚠️ Cuenta '{account.name}' sin usuarios")
        
        if problems:
            for problem in problems:
                print(f"   {problem}")
        else:
            print("   ✅ No se detectaron problemas")
        
        # 5. Proponer soluciones
        print("\n5. 🔧 SOLUCIONES PROPUESTAS:")
        
        if legacy_apartments:
            print("   📦 MIGRACIÓN DE APARTAMENTOS LEGACY:")
            print("   - Crear cuenta por defecto si no existe")
            print("   - Migrar apartamentos legacy a cuentas basándose en owner_email")
            print("   - Crear usuarios si no existen")
        
        return {
            'accounts': len(accounts),
            'legacy_apartments': len(legacy_apartments),
            'users': len(users),
            'problems': problems
        }
        
    except Exception as e:
        print(f"❌ Error en diagnóstico: {e}")
        return {'error': str(e)}
    finally:
        db.close()

def fix_multitenancy():
    """Arreglar problemas de multitenancy"""
    
    db = SessionLocal()
    try:
        print("\n🔧 ARREGLANDO MULTITENANCY")
        print("=" * 50)
        
        # 1. Migrar apartamentos legacy
        legacy_apartments = db.query(Apartment).filter(Apartment.account_id == None).all()
        
        if legacy_apartments:
            print(f"\n📦 Migrando {len(legacy_apartments)} apartamentos legacy...")
            
            for apt in legacy_apartments:
                if apt.owner_email:
                    # Buscar o crear cuenta para este email
                    account = db.query(Account).filter(Account.contact_email == apt.owner_email).first()
                    
                    if not account:
                        # Crear cuenta nueva
                        from app.auth_multiuser import create_account_slug, ensure_unique_slug
                        
                        account_name = f"Cuenta de {apt.owner_email.split('@')[0]}"
                        base_slug = create_account_slug(account_name)
                        unique_slug = ensure_unique_slug(db, base_slug)
                        
                        account = Account(
                            name=account_name,
                            slug=unique_slug,
                            contact_email=apt.owner_email,
                            max_apartments=50,
                            is_active=True
                        )
                        db.add(account)
                        db.flush()
                        
                        print(f"   ✅ Cuenta creada: {account.name} (@{account.slug})")
                        
                        # Buscar o crear usuario
                        user = db.query(User).filter(User.email == apt.owner_email).first()
                        if not user:
                            from app.auth_multiuser import get_password_hash
                            
                            user = User(
                                email=apt.owner_email,
                                full_name=f"Usuario {apt.owner_email.split('@')[0]}",
                                password_hash=get_password_hash("123456"),  # Contraseña temporal
                                is_active=True
                            )
                            db.add(user)
                            db.flush()
                            
                            print(f"   ✅ Usuario creado: {user.email} (contraseña temporal: 123456)")
                        
                        # Crear membresía
                        from datetime import datetime, timezone
                        membership = AccountUser(
                            account_id=account.id,
                            user_id=user.id,
                            role="owner",
                            invitation_accepted_at=datetime.now(timezone.utc)
                        )
                        db.add(membership)
                        
                        print(f"   ✅ Membresía creada: {user.email} → {account.name}")
                    
                    # Migrar apartamento a la cuenta
                    apt.account_id = account.id
                    print(f"   🏠 Apartamento migrado: {apt.code} → {account.name}")
        
        # 2. Verificar que todos los apartamentos tengan cuenta
        orphan_apartments = db.query(Apartment).filter(Apartment.account_id == None).all()
        
        if orphan_apartments:
            # Crear cuenta "Sistema" para apartamentos huérfanos
            sistema_account = db.query(Account).filter(Account.slug == "sistema").first()
            if not sistema_account:
                sistema_account = Account(
                    name="Sistema",
                    slug="sistema",
                    contact_email="admin@sesgas.com",
                    description="Cuenta del sistema para apartamentos legacy",
                    max_apartments=1000,
                    is_active=True
                )
                db.add(sistema_account)
                db.flush()
                print(f"   ✅ Cuenta sistema creada")
            
            for apt in orphan_apartments:
                apt.account_id = sistema_account.id
                print(f"   🏠 Apartamento huérfano migrado a sistema: {apt.code}")
        
        db.commit()
        print(f"\n🎉 Multitenancy arreglado exitosamente!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error arreglando multitenancy: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🏠 SES.GASTOS - Diagnóstico y Reparación de Multitenancy")
    
    # Diagnóstico
    diagnosis = diagnose_multitenancy()
    
    # Si hay problemas, preguntar si arreglar
    if diagnosis and diagnosis.get('problems'):
        response = input(f"\n❓ ¿Arreglar problemas detectados? (y/N): ").lower().strip()
        if response == 'y':
            success = fix_multitenancy()
            if success:
                print("\n✅ ¡Multitenancy arreglado! Ejecuta el diagnóstico de nuevo para verificar.")
            else:
                print("\n❌ Error arreglando multitenancy.")
    else:
        print("\n✅ Multitenancy funcionando correctamente!")