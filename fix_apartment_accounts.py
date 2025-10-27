#!/usr/bin/env python3
"""
Script para migrar apartamentos a las cuentas correctas
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal
from app.models import Apartment, Account, User, AccountUser

def fix_apartment_accounts():
    """Migrar apartamentos legacy a cuentas de usuario"""
    
    db = SessionLocal()
    try:
        print("🔍 Analizando apartamentos y cuentas...")
        
        # Obtener apartamentos sin cuenta (legacy)
        legacy_apartments = db.query(Apartment).filter(
            Apartment.account_id == None
        ).all()
        
        # Obtener apartamentos en cuenta "sistema"
        sistema_account = db.query(Account).filter(Account.slug == "sistema").first()
        sistema_apartments = []
        if sistema_account:
            sistema_apartments = db.query(Apartment).filter(
                Apartment.account_id == sistema_account.id
            ).all()
        
        print(f"📊 Apartamentos legacy (sin cuenta): {len(legacy_apartments)}")
        print(f"📊 Apartamentos en cuenta 'sistema': {len(sistema_apartments)}")
        
        # Mostrar apartamentos problemáticos
        all_problematic = legacy_apartments + sistema_apartments
        if all_problematic:
            print("\n🏠 Apartamentos que necesitan migración:")
            for apt in all_problematic:
                print(f"  - {apt.code}: {apt.name} (Owner: {apt.owner_email})")
        
        # Obtener cuentas de usuario reales
        user_accounts = db.query(Account).filter(
            Account.slug != "sistema"
        ).all()
        
        print(f"\n👥 Cuentas de usuario disponibles: {len(user_accounts)}")
        for account in user_accounts:
            users = db.query(AccountUser).filter(AccountUser.account_id == account.id).count()
            apartments_count = db.query(Apartment).filter(Apartment.account_id == account.id).count()
            print(f"  - {account.name} (@{account.slug}): {users} usuarios, {apartments_count} apartamentos")
        
        # Proponer migración automática
        if all_problematic and user_accounts:
            print(f"\n🔧 PROPUESTA DE MIGRACIÓN:")
            
            # Estrategia: migrar por email del owner
            migration_plan = {}
            
            for apt in all_problematic:
                if apt.owner_email:
                    # Buscar cuenta que coincida con el email
                    matching_account = None
                    for account in user_accounts:
                        if account.contact_email == apt.owner_email:
                            matching_account = account
                            break
                    
                    if matching_account:
                        if matching_account.id not in migration_plan:
                            migration_plan[matching_account.id] = {
                                'account': matching_account,
                                'apartments': []
                            }
                        migration_plan[matching_account.id]['apartments'].append(apt)
                    else:
                        print(f"  ⚠️ {apt.code}: No se encontró cuenta para {apt.owner_email}")
            
            # Mostrar plan de migración
            for account_id, plan in migration_plan.items():
                account = plan['account']
                apartments = plan['apartments']
                print(f"\n  📦 Migrar a '{account.name}' (@{account.slug}):")
                for apt in apartments:
                    print(f"    - {apt.code}: {apt.name}")
            
            # Ejecutar migración si el usuario confirma
            if migration_plan:
                response = input(f"\n❓ ¿Ejecutar migración? (y/N): ").lower().strip()
                
                if response == 'y':
                    print("\n🚀 Ejecutando migración...")
                    
                    for account_id, plan in migration_plan.items():
                        account = plan['account']
                        apartments = plan['apartments']
                        
                        for apt in apartments:
                            old_account = apt.account_id
                            apt.account_id = account.id
                            print(f"  ✅ {apt.code} → {account.name}")
                    
                    db.commit()
                    print(f"\n🎉 Migración completada exitosamente!")
                    print(f"📱 Ahora ve a https://ses-gastos.onrender.com/multiuser/dashboard")
                    print(f"🔄 Refresca la página para ver tus apartamentos")
                    
                else:
                    print("❌ Migración cancelada")
            else:
                print("❌ No se pudo crear plan de migración automática")
        
        else:
            print("✅ No hay apartamentos que necesiten migración")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_apartment_accounts()