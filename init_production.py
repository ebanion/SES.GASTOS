#!/usr/bin/env python3
"""
Script de inicialización para producción en Render
"""
import os
import sys
from datetime import datetime

def setup_production_environment():
    """Configurar entorno de producción"""
    print("🚀 INICIALIZANDO ENTORNO DE PRODUCCIÓN - SES.GASTOS")
    print("=" * 60)
    
    # Verificar variables de entorno críticas
    required_vars = {
        'DATABASE_URL': 'URL de base de datos PostgreSQL',
        'DATABASE_PRIVATE_URL': 'URL privada de base de datos (alternativa)',
        'POSTGRES_URL': 'URL de PostgreSQL (alternativa)'
    }
    
    optional_vars = {
        'TELEGRAM_TOKEN': 'Token del bot de Telegram',
        'OPENAI_API_KEY': 'Clave de API de OpenAI',
        'ADMIN_KEY': 'Clave de administrador',
        'INTERNAL_KEY': 'Clave interna (alternativa)',
        'API_BASE_URL': 'URL base de la API'
    }
    
    print("\n1. VERIFICANDO VARIABLES DE ENTORNO:")
    
    # Variables requeridas
    database_configured = False
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            masked = f"***{value[-10:]}" if len(value) > 10 else "***"
            print(f"   ✅ {var}: {masked} ({description})")
            database_configured = True
        else:
            print(f"   ⚠️ {var}: NO CONFIGURADA ({description})")
    
    if not database_configured:
        print("\n❌ CRÍTICO: No hay base de datos configurada")
        print("💡 Configura al menos una de estas variables:")
        for var in required_vars.keys():
            print(f"   - {var}")
        return False
    
    # Variables opcionales
    print("\n   Variables opcionales:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            masked = f"***{value[-4:]}" if len(value) > 4 else "***"
            print(f"   ✅ {var}: {masked}")
        else:
            print(f"   ⚠️ {var}: NO CONFIGURADA")
    
    return True

def initialize_database():
    """Inicializar base de datos en producción"""
    print("\n2. INICIALIZANDO BASE DE DATOS:")
    
    try:
        sys.path.append('.')
        from app.db import test_connection, create_tables, DATABASE_URL
        
        # Mostrar información de conexión
        if "postgresql" in DATABASE_URL:
            print("   🐘 Usando PostgreSQL")
        else:
            print("   📁 Usando SQLite")
        
        # Probar conexión
        if not test_connection():
            print("   ❌ Error de conexión a base de datos")
            return False
        print("   ✅ Conexión exitosa")
        
        # Crear tablas
        if not create_tables():
            print("   ❌ Error creando tablas")
            return False
        print("   ✅ Tablas creadas/verificadas")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def create_initial_data():
    """Crear datos iniciales si no existen"""
    print("\n3. VERIFICANDO DATOS INICIALES:")
    
    try:
        from app.db import SessionLocal
        from app import models
        from datetime import date, timedelta
        
        db = SessionLocal()
        try:
            # Verificar apartamentos
            apartments_count = db.query(models.Apartment).count()
            
            if apartments_count == 0:
                print("   📝 Creando apartamentos por defecto...")
                
                # Crear apartamentos
                default_apartments = [
                    {"code": "SES01", "name": "Apartamento Centro", "owner_email": "admin@sesgas.com"},
                    {"code": "SES02", "name": "Apartamento Playa", "owner_email": "admin@sesgas.com"},
                    {"code": "SES03", "name": "Apartamento Montaña", "owner_email": "admin@sesgas.com"}
                ]
                
                created_apartments = []
                for apt_data in default_apartments:
                    apt = models.Apartment(
                        code=apt_data["code"],
                        name=apt_data["name"],
                        owner_email=apt_data["owner_email"],
                        is_active=True
                    )
                    db.add(apt)
                    created_apartments.append(apt)
                
                db.commit()
                
                # Refresh para obtener IDs
                for apt in created_apartments:
                    db.refresh(apt)
                
                print(f"   ✅ Creados {len(created_apartments)} apartamentos")
                
                # Crear datos de demostración solo en desarrollo
                if os.getenv('RENDER_SERVICE_NAME'):  # En producción de Render
                    print("   ℹ️ Producción: No creando datos de demo")
                else:
                    print("   📊 Creando datos de demostración...")
                    
                    # Gasto de demo
                    expense = models.Expense(
                        apartment_id=created_apartments[0].id,
                        date=date.today(),
                        amount_gross=50.00,
                        currency="EUR",
                        category="Configuración",
                        description="Gasto inicial de configuración",
                        vendor="Sistema",
                        source="production_init"
                    )
                    db.add(expense)
                    
                    # Ingreso de demo
                    income = models.Income(
                        apartment_id=created_apartments[0].id,
                        date=date.today(),
                        amount_gross=100.00,
                        currency="EUR",
                        status="CONFIRMED",
                        source="production_init",
                        guest_name="Cliente Inicial",
                        guest_email="inicial@sesgas.com"
                    )
                    db.add(income)
                    
                    db.commit()
                    print("   ✅ Datos de demostración creados")
            else:
                print(f"   ℹ️ Ya existen {apartments_count} apartamentos")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"   ❌ Error creando datos iniciales: {e}")
        return False

def verify_production_setup():
    """Verificar que todo esté configurado correctamente"""
    print("\n4. VERIFICACIÓN FINAL:")
    
    try:
        from app.db import SessionLocal
        from app import models
        
        db = SessionLocal()
        try:
            # Contar registros
            counts = {
                'apartamentos': db.query(models.Apartment).count(),
                'gastos': db.query(models.Expense).count(),
                'ingresos': db.query(models.Income).count(),
                'reservas': db.query(models.Reservation).count(),
                'usuarios': db.query(models.User).count()
            }
            
            print("   📊 Estado de la base de datos:")
            for table, count in counts.items():
                print(f"      - {table.capitalize()}: {count}")
            
            # Verificar apartamentos específicos
            apartments = db.query(models.Apartment).limit(3).all()
            if apartments:
                print("   🏠 Apartamentos disponibles:")
                for apt in apartments:
                    print(f"      - {apt.code}: {apt.name}")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"   ❌ Error en verificación: {e}")
        return False

def main():
    """Función principal"""
    start_time = datetime.now()
    
    try:
        # 1. Configurar entorno
        if not setup_production_environment():
            print("\n❌ ERROR EN CONFIGURACIÓN DE ENTORNO")
            return False
        
        # 2. Inicializar base de datos
        if not initialize_database():
            print("\n❌ ERROR EN INICIALIZACIÓN DE BASE DE DATOS")
            return False
        
        # 3. Crear datos iniciales
        if not create_initial_data():
            print("\n❌ ERROR CREANDO DATOS INICIALES")
            return False
        
        # 4. Verificar configuración
        if not verify_production_setup():
            print("\n❌ ERROR EN VERIFICACIÓN FINAL")
            return False
        
        # Éxito
        elapsed = datetime.now() - start_time
        print(f"\n🎉 INICIALIZACIÓN COMPLETADA EXITOSAMENTE")
        print(f"⏱️ Tiempo transcurrido: {elapsed.total_seconds():.2f} segundos")
        
        print(f"\n🌐 ENDPOINTS DISPONIBLES:")
        print(f"   - Health: /health")
        print(f"   - API Status: /db-status")
        print(f"   - Dashboard: /api/v1/dashboard/")
        print(f"   - Bot Status: /bot/status")
        
        if os.getenv('TELEGRAM_TOKEN'):
            print(f"\n🤖 BOT TELEGRAM:")
            print(f"   - Configurar webhook: POST /bot/setup-webhook")
            print(f"   - Estado webhook: GET /bot/webhook-status")
            print(f"   - Diagnóstico: GET /bot/diagnose")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)