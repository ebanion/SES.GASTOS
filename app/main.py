# app/main.py
import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

# Importa modelos para que SQLAlchemy “conozca” las tablas
from . import models  # noqa

from .db import Base, engine

# Importaciones básicas primero
try:
    from .routers import auth, apartments, incomes, reservations, expenses, admin, public, user_dashboard, email_setup, email_webhooks, vectors
    print("[import] ✅ Routers básicos importados")
except Exception as e:
    print(f"[import] ❌ Error en routers básicos: {e}")

try:
    from .dashboard_api import router as dashboard_router
    print("[import] ✅ Dashboard importado")
except Exception as e:
    print(f"[import] ❌ Error en dashboard: {e}")
    dashboard_router = None



app = FastAPI(title="SES.GASTOS")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Crear/migrar tablas al arrancar
@app.on_event("startup")
def on_startup() -> None:
    """Inicialización de la aplicación al arrancar"""
    print("[startup] 🚀 Iniciando SES.GASTOS...")
    
    # Verificar conexión de base de datos
    try:
        from .db import test_connection, create_tables
        if test_connection():
            print("[startup] ✅ Base de datos conectada")
            
            # Crear tablas si no existen
            if create_tables():
                print("[startup] ✅ Tablas verificadas/creadas")
            else:
                print("[startup] ⚠️ Problema creando tablas")
        else:
            print("[startup] ❌ Error de conexión a base de datos")
            return
            
    except Exception as db_error:
        print(f"[startup] ❌ Error de base de datos: {db_error}")
        return
    
    # Inicializar datos básicos si no existen
    try:
        from .db import SessionLocal
        from . import models
        from datetime import date, timedelta
        
        db = SessionLocal()
        try:
            existing_apartments = db.query(models.Apartment).count()
            
            if existing_apartments == 0:
                print("[startup] 📝 Creando apartamentos por defecto...")
                
                # Crear apartamentos por defecto
                default_apartments_data = [
                    {"code": "SES01", "name": "Apartamento Centro", "owner_email": "admin@sesgas.com"},
                    {"code": "SES02", "name": "Apartamento Playa", "owner_email": "admin@sesgas.com"},
                    {"code": "SES03", "name": "Apartamento Montaña", "owner_email": "admin@sesgas.com"}
                ]
                
                created_apartments = []
                for apt_data in default_apartments_data:
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
                
                print(f"[startup] ✅ Creados {len(created_apartments)} apartamentos")
                
                # Crear datos de demostración
                try:
                    # Gastos de demo
                    expenses_demo = [
                        {"amount": 45.50, "category": "Restauración", "vendor": "Restaurante Demo", "description": "Cena de negocios"},
                        {"amount": 25.00, "category": "Transporte", "vendor": "Taxi Express", "description": "Traslado aeropuerto"},
                        {"amount": 80.75, "category": "Limpieza", "vendor": "Clean Pro", "description": "Limpieza profunda"},
                        {"amount": 35.00, "category": "Suministros", "vendor": "Ferretería Local", "description": "Material de reparación"}
                    ]
                    
                    for exp_data in expenses_demo:
                        expense = models.Expense(
                            apartment_id=created_apartments[0].id,
                            date=date.today(),
                            amount_gross=exp_data["amount"],
                            currency="EUR",
                            category=exp_data["category"],
                            description=exp_data["description"],
                            vendor=exp_data["vendor"],
                            source="demo_startup"
                        )
                        db.add(expense)
                    
                    # Reserva de demo
                    reservation = models.Reservation(
                        apartment_id=created_apartments[0].id,
                        check_in=date.today() + timedelta(days=2),
                        check_out=date.today() + timedelta(days=6),
                        guests=2,
                        channel="Booking.com",
                        email_contact="demo@example.com",
                        phone_contact="+34123456789",
                        status="CONFIRMED"
                    )
                    db.add(reservation)
                    db.flush()  # Para obtener ID
                    
                    # Ingresos de demo
                    incomes_demo = [
                        {"amount": 200.00, "status": "CONFIRMED", "source": "booking_com", "guest": "Juan Pérez"},
                        {"amount": 150.00, "status": "CONFIRMED", "source": "airbnb", "guest": "María García"},
                        {"amount": 180.00, "status": "PENDING", "source": "direct", "guest": "Carlos López"}
                    ]
                    
                    for inc_data in incomes_demo:
                        income = models.Income(
                            apartment_id=created_apartments[0].id,
                            reservation_id=reservation.id if inc_data["status"] == "CONFIRMED" else None,
                            date=date.today(),
                            amount_gross=inc_data["amount"],
                            currency="EUR",
                            status=inc_data["status"],
                            source=inc_data["source"],
                            guest_name=inc_data["guest"],
                            guest_email=f"{inc_data['guest'].lower().replace(' ', '.')}@example.com"
                        )
                        db.add(income)
                    
                    db.commit()
                    print(f"[startup] ✅ Datos demo: {len(expenses_demo)} gastos, 1 reserva, {len(incomes_demo)} ingresos")
                    
                except Exception as demo_error:
                    print(f"[startup] ⚠️ Error creando datos demo: {demo_error}")
                    db.rollback()
            else:
                print(f"[startup] ℹ️ Encontrados {existing_apartments} apartamentos existentes")
                
        finally:
            db.close()
            
    except Exception as init_error:
        print(f"[startup] ❌ Error inicializando datos: {init_error}")
    
    # Configuración de bot (deshabilitado temporalmente)
    print("[startup] ⚠️ Bot Telegram configurado para webhooks")
    print("[startup] 🎉 SES.GASTOS iniciado correctamente")

@app.on_event("shutdown")
def on_shutdown() -> None:
    try:
        from .telegram_bot_service import telegram_service
        telegram_service.stop_bot()
        print("[shutdown] ✅ Telegram bot detenido correctamente")
    except Exception as e:
        print(f"[shutdown] Error stopping bot: {e}")

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/force-postgres")
def force_postgres_connection():
    """Forzar cambio a PostgreSQL en tiempo real"""
    import os
    from sqlalchemy import create_engine, text
    from app.db import SessionLocal
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url or "postgresql" not in database_url:
        return {"error": "DATABASE_URL PostgreSQL no configurada"}
    
    try:
        # Crear nuevo engine PostgreSQL
        pg_engine = create_engine(
            database_url, 
            pool_pre_ping=True,
            connect_args={"connect_timeout": 30, "application_name": "ses-gastos-force"}
        )
        
        # Test de conexión
        with pg_engine.connect() as conn:
            version = conn.execute(text("SELECT version()")).scalar()
            
        # Crear tablas si no existen
        from app.db import Base
        from app import models  # Importar modelos
        Base.metadata.create_all(bind=pg_engine)
        
        # Actualizar engine global (¡PELIGROSO pero necesario!)
        import app.db
        from sqlalchemy.orm import sessionmaker
        app.db.engine = pg_engine
        app.db.DATABASE_URL = database_url
        app.db.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)
        
        return {
            "success": True,
            "message": "✅ PostgreSQL forzado exitosamente",
            "database_url": database_url.replace(database_url.split('@')[0].split(':')[-1], '***'),
            "postgres_version": version.split()[1],
            "warning": "Cambio aplicado en tiempo real - puede requerir reinicio para estabilidad"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "❌ No se pudo forzar PostgreSQL"
        }

@app.post("/init-postgres-tables")
def init_postgres_tables():
    """Inicializar tablas en PostgreSQL y crear datos demo"""
    import os
    from sqlalchemy import create_engine, text
    from datetime import date, timedelta
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url or "postgresql" not in database_url:
        return {"error": "DATABASE_URL PostgreSQL no configurada"}
    
    try:
        # Conectar a PostgreSQL
        pg_engine = create_engine(
            database_url, 
            pool_pre_ping=True,
            connect_args={"connect_timeout": 30}
        )
        
        # Crear todas las tablas
        from app.db import Base
        from app import models
        Base.metadata.create_all(bind=pg_engine)
        
        # Crear sesión para datos demo
        from sqlalchemy.orm import sessionmaker
        SessionPG = sessionmaker(bind=pg_engine)
        db = SessionPG()
        
        try:
            # Verificar si ya hay apartamentos
            existing_apartments = db.query(models.Apartment).count()
            
            if existing_apartments == 0:
                # Crear apartamentos demo
                apartments_demo = [
                    {"code": "SES01", "name": "Apartamento Centro", "owner_email": "demo@sesgas.com"},
                    {"code": "SES02", "name": "Apartamento Playa", "owner_email": "demo@sesgas.com"},
                    {"code": "SES03", "name": "Apartamento Montaña", "owner_email": "demo@sesgas.com"}
                ]
                
                created_apartments = []
                for apt_data in apartments_demo:
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
                
                # Crear gastos demo
                expenses_demo = [
                    {"amount": 45.50, "category": "Restauración", "vendor": "Restaurante Demo"},
                    {"amount": 25.00, "category": "Transporte", "vendor": "Taxi Express"},
                    {"amount": 80.75, "category": "Limpieza", "vendor": "Clean Pro"},
                    {"amount": 35.00, "category": "Suministros", "vendor": "Ferretería"}
                ]
                
                for exp_data in expenses_demo:
                    expense = models.Expense(
                        apartment_id=created_apartments[0].id,  # SES01
                        date=date.today(),
                        amount_gross=exp_data["amount"],
                        currency="EUR",
                        category=exp_data["category"],
                        vendor=exp_data["vendor"],
                        description=f"Demo - {exp_data['vendor']}",
                        source="postgres_init"
                    )
                    db.add(expense)
                
                # Crear ingresos demo
                incomes_demo = [
                    {"amount": 200.00, "status": "CONFIRMED", "guest": "Juan Pérez"},
                    {"amount": 150.00, "status": "CONFIRMED", "guest": "María García"},
                    {"amount": 180.00, "status": "PENDING", "guest": "Carlos López"}
                ]
                
                for inc_data in incomes_demo:
                    income = models.Income(
                        apartment_id=created_apartments[0].id,
                        date=date.today(),
                        amount_gross=inc_data["amount"],
                        currency="EUR",
                        status=inc_data["status"],
                        source="postgres_init",
                        guest_name=inc_data["guest"],
                        guest_email=f"{inc_data['guest'].lower().replace(' ', '.')}@example.com"
                    )
                    db.add(income)
                
                db.commit()
                
                return {
                    "success": True,
                    "message": "✅ PostgreSQL inicializado con datos demo",
                    "created": {
                        "apartments": len(created_apartments),
                        "expenses": len(expenses_demo),
                        "incomes": len(incomes_demo)
                    },
                    "apartment_codes": [apt.code for apt in created_apartments]
                }
            else:
                return {
                    "success": True,
                    "message": f"PostgreSQL ya tiene {existing_apartments} apartamentos",
                    "existing_apartments": existing_apartments
                }
                
        finally:
            db.close()
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "❌ Error inicializando PostgreSQL"
        }

@app.post("/migrate-postgres")
def migrate_postgres():
    """Migrar estructura de PostgreSQL y agregar columnas faltantes"""
    import os
    from sqlalchemy import create_engine, text
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url or "postgresql" not in database_url:
        return {"error": "DATABASE_URL PostgreSQL no configurada"}
    
    try:
        # Conectar a PostgreSQL
        pg_engine = create_engine(database_url, pool_pre_ping=True)
        
        migrations = []
        
        with pg_engine.connect() as conn:
            # Migración 1: Agregar user_id a apartments si no existe
            try:
                conn.execute(text("ALTER TABLE apartments ADD COLUMN IF NOT EXISTS user_id VARCHAR(36)"))
                migrations.append("✅ Columna user_id agregada a apartments")
            except Exception as e:
                migrations.append(f"⚠️ user_id en apartments: {e}")
            
            # Migración 2: Crear tabla users si no existe
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        full_name VARCHAR(255) NOT NULL,
                        password_hash TEXT NOT NULL,
                        phone VARCHAR(50),
                        company VARCHAR(255),
                        is_active BOOLEAN DEFAULT true,
                        is_admin BOOLEAN DEFAULT false,
                        last_login TIMESTAMP WITH TIME ZONE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """))
                migrations.append("✅ Tabla users creada/verificada")
            except Exception as e:
                migrations.append(f"⚠️ Tabla users: {e}")
            
            # Migración 3: Agregar foreign key (sin IF NOT EXISTS)
            try:
                # Primero verificar si existe
                fk_check = conn.execute(text("""
                    SELECT COUNT(*) FROM information_schema.table_constraints 
                    WHERE constraint_name = 'apartments_user_id_fkey' 
                    AND table_name = 'apartments'
                """)).scalar()
                
                if fk_check == 0:
                    conn.execute(text("""
                        ALTER TABLE apartments 
                        ADD CONSTRAINT apartments_user_id_fkey 
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                    """))
                    migrations.append("✅ Foreign key apartments->users agregada")
                else:
                    migrations.append("✅ Foreign key apartments->users ya existe")
            except Exception as e:
                migrations.append(f"⚠️ Foreign key: {e}")
            
            conn.commit()
        
        # Migración 4: Crear todas las tablas usando SQLAlchemy
        try:
            from app.db import Base
            from app import models
            Base.metadata.create_all(bind=pg_engine)
            migrations.append("✅ Todas las tablas creadas con SQLAlchemy")
        except Exception as e:
            migrations.append(f"⚠️ SQLAlchemy create_all: {e}")
        
        # Migración 5: Verificar tablas finales
        with pg_engine.connect() as conn:
            tables_to_check = ["users", "apartments", "expenses", "incomes", "reservations"]
            for table in tables_to_check:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    migrations.append(f"✅ Tabla {table}: {count} registros")
                except Exception as e:
                    migrations.append(f"❌ Tabla {table}: {e}")
        
        return {
            "success": True,
            "message": "✅ Migración completada",
            "migrations": migrations,
            "next_step": "Usar /init-postgres-tables para crear datos demo"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "❌ Error en migración"
        }

@app.post("/create-tables-force")
def create_tables_force():
    """Forzar creación de tablas en la base de datos actual"""
    try:
        from app.db import engine, Base
        from app import models  # Importar todos los modelos
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        
        # Verificar que se crearon
        from sqlalchemy import text
        tables_created = []
        
        with engine.connect() as conn:
            for table_name in ["users", "apartments", "expenses", "incomes", "reservations"]:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    tables_created.append(f"✅ {table_name}: {count} registros")
                except Exception as e:
                    tables_created.append(f"❌ {table_name}: {e}")
        
        return {
            "success": True,
            "message": "✅ Tablas creadas forzadamente",
            "tables": tables_created,
            "database_url": "SQLite" if "sqlite" in str(engine.url) else "PostgreSQL"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "❌ Error creando tablas"
        }

@app.get("/test-postgres")
def test_postgres_direct():
    """Probar conexión directa a PostgreSQL"""
    import os
    from sqlalchemy import create_engine, text
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return {"error": "DATABASE_URL no configurada"}
    
    # Mostrar URL (enmascarada)
    import re
    masked_url = re.sub(r"://([^:@]+):[^@]+@", r"://\1:***@", database_url)
    
    try:
        # Probar conexión directa sin fallback
        engine = create_engine(database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()")).scalar()
            return {
                "success": True,
                "database_url": masked_url,
                "postgres_version": result,
                "message": "✅ PostgreSQL conectado exitosamente"
            }
    except Exception as e:
        return {
            "success": False,
            "database_url": masked_url,
            "error": str(e),
            "error_type": type(e).__name__,
            "message": "❌ Error conectando a PostgreSQL"
        }

@app.get("/db-status")
def db_status():
    """Check database connection status"""
    try:
        from app.db import engine, DATABASE_URL
        from sqlalchemy import text
        import os
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Información detallada de la base de datos
        return {
            "database": "connected", 
            "status": "ok",
            "database_url": DATABASE_URL,
            "database_type": "postgresql" if "postgresql" in DATABASE_URL else "sqlite",
            "environment_vars": {
                "DATABASE_URL": "***" + os.getenv("DATABASE_URL", "NOT_SET")[-20:] if os.getenv("DATABASE_URL") else "NOT_SET",
                "POSTGRES_URL": "***" + os.getenv("POSTGRES_URL", "NOT_SET")[-20:] if os.getenv("POSTGRES_URL") else "NOT_SET",
                "DATABASE_PRIVATE_URL": "***" + os.getenv("DATABASE_PRIVATE_URL", "NOT_SET")[-20:] if os.getenv("DATABASE_PRIVATE_URL") else "NOT_SET"
            }
        }
    except Exception as e:
        return {"database": "disconnected", "error": str(e), "status": "error"}

@app.get("/")
def root():
    return {
        "message": "🏠 SES.GASTOS - Sistema de Gestión de Gastos",
        "status": "active",
        "auth": "/auth/",
        "dashboard": "/dashboard/",
        "health": "/health"
    }

@app.get("/dashboard")
def dashboard_redirect():
    return RedirectResponse(url="/api/v1/dashboard/")

# Incluir routers básicos solamente
try:
    app.include_router(auth.router)
    print("[router] ✅ Auth router incluido")
except Exception as e:
    print(f"[router] ❌ Error incluyendo auth: {e}")

try:
    app.include_router(apartments.router)
    print("[router] ✅ Apartments router incluido")
except Exception as e:
    print(f"[router] ❌ Error incluyendo apartments: {e}")

try:
    app.include_router(incomes.router)
    print("[router] ✅ Incomes router incluido")
except Exception as e:
    print(f"[router] ❌ Error incluyendo incomes: {e}")

try:
    app.include_router(reservations.router)
    print("[router] ✅ Reservations router incluido")
except Exception as e:
    print(f"[router] ❌ Error incluyendo reservations: {e}")

try:
    app.include_router(expenses.router)
    print("[router] ✅ Expenses router incluido")
except Exception as e:
    print(f"[router] ❌ Error incluyendo expenses: {e}")

try:
    app.include_router(admin.router)
    print("[router] ✅ Admin router incluido")
except Exception as e:
    print(f"[router] ❌ Error incluyendo admin: {e}")

try:
    app.include_router(public.router)
    print("[router] ✅ Public router incluido")
except Exception as e:
    print(f"[router] ❌ Error incluyendo public: {e}")

try:
    app.include_router(user_dashboard.router)
    print("[router] ✅ User dashboard router incluido")
except Exception as e:
    print(f"[router] ❌ Error incluyendo user_dashboard: {e}")

try:
    app.include_router(email_setup.router)
    print("[router] ✅ Email setup router incluido")
except Exception as e:
    print(f"[router] ❌ Error incluyendo email_setup: {e}")

try:
    app.include_router(email_webhooks.router)
    print("[router] ✅ Email webhooks router incluido")
except Exception as e:
    print(f"[router] ❌ Error incluyendo email_webhooks: {e}")

try:
    app.include_router(vectors.router)
    print("[router] ✅ Vectors router incluido")
except Exception as e:
    print(f"[router] ❌ Error incluyendo vectors: {e}")

# Agregar webhook de Telegram para producción
try:
    from .webhook_bot import webhook_router
    app.include_router(webhook_router)
    print("[router] ✅ Telegram webhook router incluido")
except Exception as e:
    print(f"[router] ❌ Error incluyendo telegram webhook: {e}")

if dashboard_router:
    try:
        app.include_router(dashboard_router)
        print("[router] ✅ Dashboard router incluido")
    except Exception as e:
        print(f"[router] ❌ Error incluyendo dashboard: {e}")

# Pequeño debug para ver rutas en producción si hace falta
@app.get("/debug/routes")
def list_routes():
    return sorted([getattr(r, "path", "") for r in app.router.routes])

@app.post("/test/create-expense")
def test_create_expense():
    """Endpoint de prueba para crear un gasto"""
    try:
        from .db import SessionLocal
        from . import models
        from datetime import date
        
        db = SessionLocal()
        
        # Buscar apartamento SES01
        apt = db.query(models.Apartment).filter(models.Apartment.code == "SES01").first()
        if not apt:
            return {"error": "Apartamento SES01 no encontrado"}
        
        # Crear gasto de prueba
        expense = models.Expense(
            apartment_id=apt.id,
            date=date.today(),
            amount_gross=45.50,
            currency="EUR",
            category="Prueba",
            description="Gasto de prueba desde endpoint",
            vendor="Vendor Test",
            source="test_endpoint"
        )
        
        db.add(expense)
        db.commit()
        db.refresh(expense)
        
        result = {
            "success": True,
            "expense_id": expense.id,
            "apartment_id": expense.apartment_id,
            "amount": float(expense.amount_gross),
            "date": str(expense.date),
            "message": "Gasto creado exitosamente"
        }
        
        db.close()
        return result
        
    except Exception as e:
        return {"error": str(e), "success": False}

@app.get("/bot/status")
def bot_status():
    """Obtener estado del bot de Telegram"""
    try:
        from .telegram_bot_service import telegram_service
        status = telegram_service.get_status()
        
        # Agregar información adicional de diagnóstico
        import os
        status.update({
            "environment_vars": {
                "TELEGRAM_TOKEN": "***" + os.getenv("TELEGRAM_TOKEN", "")[-4:] if os.getenv("TELEGRAM_TOKEN") else None,
                "OPENAI_API_KEY": "***" + os.getenv("OPENAI_API_KEY", "")[-4:] if os.getenv("OPENAI_API_KEY") else None,
                "INTERNAL_KEY": bool(os.getenv("INTERNAL_KEY") or os.getenv("ADMIN_KEY")),
                "API_BASE_URL": os.getenv("API_BASE_URL", "not_set")
            },
            "apartments_available": None  # Lo llenaremos después
        })
        
        # Verificar apartamentos disponibles
        try:
            from .db import SessionLocal
            from . import models
            db = SessionLocal()
            apartments_count = db.query(models.Apartment).count()
            apartments = db.query(models.Apartment).limit(5).all()
            status["apartments_available"] = {
                "count": apartments_count,
                "codes": [apt.code for apt in apartments]
            }
            db.close()
        except Exception as e:
            status["apartments_available"] = {"error": str(e)}
        
        return status
    except Exception as e:
        return {"error": str(e), "bot_running": False}

@app.post("/bot/restart")
def restart_bot():
    """Reiniciar el bot de Telegram"""
    try:
        from .telegram_bot_service import telegram_service
        telegram_service.stop_bot()
        import time
        time.sleep(3)  # Esperar más tiempo antes de reiniciar
        telegram_service.start_bot_in_thread()
        return {"success": True, "message": "Bot reiniciado con versión de producción"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/bot/test-simple")
def test_simple_bot():
    """Probar bot simple sin iniciar hilo"""
    try:
        import os
        token = os.getenv("TELEGRAM_TOKEN")
        if not token:
            return {"success": False, "error": "TELEGRAM_TOKEN no configurado"}
        
        # Probar conexión básica con Telegram API
        import requests
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()["result"]
            return {
                "success": True, 
                "bot_info": {
                    "username": bot_info.get("username"),
                    "first_name": bot_info.get("first_name"),
                    "id": bot_info.get("id")
                },
                "message": f"✅ Bot @{bot_info.get('username')} conectado correctamente",
                "instructions": [
                    f"1. Busca @{bot_info.get('username')} en Telegram",
                    "2. Envía /start",
                    "3. Envía /usar SES01", 
                    "4. Envía foto de factura o datos manuales",
                    "5. Ve el resultado en el dashboard"
                ]
            }
        else:
            return {
                "success": False, 
                "error": f"Error HTTP {response.status_code}: {response.text}"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/bot/test-connection")
def test_bot_connection():
    """Probar conexión del bot con Telegram"""
    try:
        import os
        token = os.getenv("TELEGRAM_TOKEN")
        if not token:
            return {"success": False, "error": "TELEGRAM_TOKEN no configurado"}
        
        # Probar conexión básica con Telegram API
        import requests
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            return {
                "success": True, 
                "bot_info": bot_info,
                "message": "Conexión con Telegram exitosa"
            }
        else:
            return {
                "success": False, 
                "error": f"Error HTTP {response.status_code}: {response.text}"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/create-demo-data-sql")
def create_demo_data_sql():
    """Crear datos de demostración usando SQL directo"""
    from .db import SessionLocal
    from sqlalchemy import text
    from datetime import date
    
    db = SessionLocal()
    try:
        # Obtener apartment_id de SES01
        result = db.execute(text("SELECT id FROM apartments WHERE code = 'SES01' LIMIT 1"))
        apartment_row = result.fetchone()
        if not apartment_row:
            return {"error": "Apartamento SES01 no encontrado"}
        
        apartment_id = apartment_row[0]
        today = date.today()
        
        # Crear múltiples gastos
        expenses_sql = """
        INSERT INTO expenses (id, apartment_id, date, amount_gross, currency, category, description, vendor, source, created_at)
        VALUES 
        (gen_random_uuid(), :apt_id, :date1, 45.50, 'EUR', 'Restauración', 'Cena en restaurante', 'Restaurante Demo', 'demo_sql', NOW()),
        (gen_random_uuid(), :apt_id, :date2, 25.00, 'EUR', 'Transporte', 'Taxi al aeropuerto', 'Taxi Express', 'demo_sql', NOW()),
        (gen_random_uuid(), :apt_id, :date3, 80.75, 'EUR', 'Limpieza', 'Limpieza profunda', 'Clean Pro', 'demo_sql', NOW()),
        (gen_random_uuid(), :apt_id, :date4, 120.00, 'EUR', 'Mantenimiento', 'Reparación fontanería', 'Fontanero 24h', 'demo_sql', NOW())
        """
        
        db.execute(text(expenses_sql), {
            'apt_id': apartment_id,
            'date1': today,
            'date2': today,
            'date3': today,
            'date4': today
        })
        
        # Crear reserva
        reservation_sql = """
        INSERT INTO reservations (id, apartment_id, check_in, check_out, guests, channel, email_contact, phone_contact, status, created_at)
        VALUES (:res_id, :apt_id, :check_in, :check_out, 2, 'Booking.com', 'demo@test.com', '+34123456789', 'CONFIRMED', NOW())
        """
        
        reservation_id = f"RES-{today.strftime('%Y%m%d')}-001"
        check_in = date(2025, 10, 26)
        check_out = date(2025, 10, 30)
        
        db.execute(text(reservation_sql), {
            'res_id': reservation_id,
            'apt_id': apartment_id,
            'check_in': check_in,
            'check_out': check_out
        })
        
        # Crear ingresos
        incomes_sql = """
        INSERT INTO incomes (id, apartment_id, reservation_id, date, amount_gross, currency, status, source, guest_name, guest_email, booking_reference, created_at)
        VALUES 
        (gen_random_uuid(), :apt_id, :res_id, :date1, 200.00, 'EUR', 'CONFIRMED', 'booking_com', 'Juan Pérez', 'demo@test.com', 'BK001', NOW()),
        (gen_random_uuid(), :apt_id, NULL, :date2, 150.00, 'EUR', 'CONFIRMED', 'airbnb', 'María García', 'maria@test.com', 'AIR002', NOW()),
        (gen_random_uuid(), :apt_id, NULL, :date3, 180.00, 'EUR', 'PENDING', 'direct', 'Carlos López', 'carlos@test.com', 'DIR003', NOW())
        """
        
        db.execute(text(incomes_sql), {
            'apt_id': apartment_id,
            'res_id': reservation_id,
            'date1': today,
            'date2': today,
            'date3': today
        })
        
        db.commit()
        
        return {
            "success": True,
            "apartment_id": apartment_id,
            "created": {
                "expenses": 4,
                "reservations": 1, 
                "incomes": 3
            },
            "totals": {
                "expenses": 45.50 + 25.00 + 80.75 + 120.00,
                "incomes_confirmed": 200.00 + 150.00,
                "incomes_pending": 180.00,
                "net_confirmed": (200.00 + 150.00) - (45.50 + 25.00 + 80.75 + 120.00)
            },
            "message": "✅ Datos de demostración creados con SQL directo"
        }
        
    except Exception as e:
        db.rollback()
        return {"error": str(e), "success": False}
    finally:
        db.close()

@app.post("/create-test-expense")
def create_test_expense():
    """Crear gasto de prueba para verificar dashboard"""
    from .db import SessionLocal
    from . import models
    from datetime import datetime, date
    
    db = SessionLocal()
    try:
        # Buscar apartamento SES01
        apt = db.query(models.Apartment).filter(models.Apartment.code == "SES01").first()
        if not apt:
            return {"error": "Apartamento SES01 no encontrado"}
        
        # Crear gasto de prueba con fecha actual
        expense = models.Expense(
            apartment_id=apt.id,
            date=date.today(),
            amount_gross=75.25,
            currency="EUR",
            category="Restauración",
            description="Gasto de prueba - Restaurante Test",
            vendor="Restaurante Ejemplo",
            source="test_manual",
            invoice_number="TEST-001"
        )
        
        db.add(expense)
        db.commit()
        db.refresh(expense)
        
        return {
            "success": True,
            "expense_id": expense.id,
            "apartment_code": "SES01",
            "apartment_id": expense.apartment_id,
            "amount": float(expense.amount_gross),
            "date": str(expense.date),
            "vendor": expense.vendor,
            "message": "✅ Gasto creado exitosamente - Debería aparecer en el dashboard"
        }
        
    except Exception as e:
        db.rollback()
        return {"error": str(e), "success": False}
    finally:
        db.close()

@app.post("/create-test-reservation")
def create_test_reservation():
    """Crear reserva de prueba para verificar dashboard"""
    from .db import SessionLocal
    from . import models
    from datetime import datetime, date, timedelta
    
    db = SessionLocal()
    try:
        # Buscar apartamento SES01
        apt = db.query(models.Apartment).filter(models.Apartment.code == "SES01").first()
        if not apt:
            return {"error": "Apartamento SES01 no encontrado"}
        
        # Crear reserva de prueba (check-in en 3 días, check-out en 7 días)
        check_in_date = date.today() + timedelta(days=3)
        check_out_date = date.today() + timedelta(days=7)
        
        reservation = models.Reservation(
            apartment_id=apt.id,
            check_in=check_in_date,
            check_out=check_out_date,
            guests=2,
            channel="Booking.com",
            email_contact="test@example.com",
            phone_contact="+34123456789",
            status="CONFIRMED"  # CONFIRMED, PENDING, CANCELLED
        )
        
        db.add(reservation)
        db.commit()
        db.refresh(reservation)
        
        return {
            "success": True,
            "reservation_id": reservation.id,
            "apartment_code": "SES01",
            "apartment_id": reservation.apartment_id,
            "check_in": str(reservation.check_in),
            "check_out": str(reservation.check_out),
            "guests": reservation.guests,
            "status": reservation.status,
            "message": "✅ Reserva creada exitosamente - Debería aparecer en el dashboard"
        }
        
    except Exception as e:
        db.rollback()
        return {"error": str(e), "success": False}
    finally:
        db.close()

@app.post("/create-test-income")
def create_test_income():
    """Crear ingreso de prueba para verificar dashboard"""
    from .db import SessionLocal
    from . import models
    from datetime import datetime, date, timedelta
    
    db = SessionLocal()
    try:
        # Buscar apartamento SES01
        apt = db.query(models.Apartment).filter(models.Apartment.code == "SES01").first()
        if not apt:
            return {"error": "Apartamento SES01 no encontrado"}
        
        # Buscar una reserva existente (opcional)
        reservation = db.query(models.Reservation).filter(
            models.Reservation.apartment_id == apt.id
        ).first()
        
        # Crear ingreso de prueba
        income = models.Income(
            apartment_id=apt.id,
            reservation_id=reservation.id if reservation else None,
            date=date.today(),
            amount_gross=150.00,
            currency="EUR",
            status="CONFIRMED",  # CONFIRMED, PENDING, CANCELLED
            source="test_manual",
            guest_name="Cliente Test",
            guest_email="test@example.com",
            booking_reference="TEST-001"
        )
        
        db.add(income)
        db.commit()
        db.refresh(income)
        
        return {
            "success": True,
            "income_id": str(income.id),
            "apartment_code": "SES01",
            "apartment_id": income.apartment_id,
            "reservation_id": income.reservation_id,
            "amount": float(income.amount_gross),
            "date": str(income.date),
            "status": income.status,
            "message": "✅ Ingreso creado exitosamente - Debería aparecer en el dashboard"
        }
        
    except Exception as e:
        db.rollback()
        return {"error": str(e), "success": False}
    finally:
        db.close()

@app.post("/create-test-complete-flow")
def create_test_complete_flow():
    """Crear flujo completo: Reserva + Ingreso + Gasto"""
    from .db import SessionLocal
    from . import models
    from datetime import datetime, date, timedelta
    
    db = SessionLocal()
    try:
        # Buscar apartamento SES01
        apt = db.query(models.Apartment).filter(models.Apartment.code == "SES01").first()
        if not apt:
            return {"error": "Apartamento SES01 no encontrado"}
        
        results = {}
        
        # 1. Crear reserva
        check_in_date = date.today() + timedelta(days=1)
        check_out_date = date.today() + timedelta(days=5)
        
        reservation = models.Reservation(
            apartment_id=apt.id,
            check_in=check_in_date,
            check_out=check_out_date,
            guests=3,
            channel="Airbnb",
            email_contact="guest@example.com",
            phone_contact="+34987654321",
            status="CONFIRMED"
        )
        db.add(reservation)
        db.flush()  # Para obtener el ID sin commit
        
        results["reservation"] = {
            "id": reservation.id,
            "check_in": str(reservation.check_in),
            "check_out": str(reservation.check_out),
            "guests": reservation.guests,
            "status": reservation.status
        }
        
        # 2. Crear ingreso asociado
        income = models.Income(
            apartment_id=apt.id,
            reservation_id=reservation.id,
            date=date.today(),
            amount_gross=200.00,
            currency="EUR",
            status="CONFIRMED",
            source="airbnb_booking",
            guest_name="Cliente Airbnb",
            guest_email="guest@example.com",
            booking_reference=f"AIR-{reservation.id[:8]}"
        )
        db.add(income)
        db.flush()
        
        results["income"] = {
            "id": str(income.id),
            "amount": float(income.amount_gross),
            "date": str(income.date),
            "status": income.status,
            "reservation_id": income.reservation_id
        }
        
        # 3. Crear gasto asociado
        expense = models.Expense(
            apartment_id=apt.id,
            date=date.today(),
            amount_gross=35.75,
            currency="EUR",
            category="Limpieza",
            description="Limpieza post check-out",
            vendor="Limpieza Express",
            source="reservation_expense"
        )
        db.add(expense)
        db.flush()
        
        results["expense"] = {
            "id": expense.id,
            "amount": float(expense.amount_gross),
            "date": str(expense.date),
            "category": expense.category,
            "vendor": expense.vendor
        }
        
        # Commit todo junto
        db.commit()
        
        # Calcular net
        net_profit = income.amount_gross - expense.amount_gross
        
        return {
            "success": True,
            "apartment_code": "SES01",
            "results": results,
            "summary": {
                "income": float(income.amount_gross),
                "expense": float(expense.amount_gross),
                "net_profit": float(net_profit)
            },
            "message": "✅ Flujo completo creado: Reserva + Ingreso + Gasto"
        }
        
    except Exception as e:
        db.rollback()
        return {"error": str(e), "success": False}
    finally:
        db.close()

@app.post("/init-demo-data")
def init_demo_data():
    """TEMPORAL: Inicializar datos de demostración (ELIMINAR EN PRODUCCIÓN)"""
    from .db import SessionLocal
    from . import models
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    try:
        # Verificar si ya hay apartamentos
        existing_apartments = db.query(models.Apartment).count()
        if existing_apartments > 0:
            return {"message": f"Ya hay {existing_apartments} apartamentos", "apartments": existing_apartments}
        
        # Crear apartamentos
        apartments_data = [
            {"code": "SES01", "name": "Apartamento Centro", "owner_email": "demo@sesgas.com"},
            {"code": "SES02", "name": "Apartamento Playa", "owner_email": "demo@sesgas.com"},
            {"code": "SES03", "name": "Apartamento Montaña", "owner_email": "demo@sesgas.com"}
        ]
        
        created_apartments = []
        for apt_data in apartments_data:
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
        
        # Crear algunos gastos de demo
        base_date = datetime.now() - timedelta(days=15)
        expenses_data = [
            {"amount": 45.50, "category": "Restauración", "vendor": "Restaurante Demo", "description": "Gasto de demostración"},
            {"amount": 25.00, "category": "Transporte", "vendor": "Taxi Demo", "description": "Traslado demo"},
            {"amount": 80.00, "category": "Servicios", "vendor": "Servicio Demo", "description": "Reparación demo"}
        ]
        
        created_expenses = []
        for i, exp_data in enumerate(expenses_data):
            apartment = created_apartments[i % len(created_apartments)]
            
            expense = models.Expense(
                apartment_id=apartment.id,
                date=(base_date + timedelta(days=i*2)).date(),
                amount_gross=exp_data["amount"],
                currency="EUR",
                category=exp_data["category"],
                description=exp_data["description"],
                vendor=exp_data["vendor"],
                source="demo_init"
            )
            db.add(expense)
            created_expenses.append(expense)
        
        # Crear algunos ingresos de demo
        incomes_data = [
            {"amount": 150.00, "status": "CONFIRMED"},
            {"amount": 200.00, "status": "CONFIRMED"},
            {"amount": 180.00, "status": "PENDING"}
        ]
        
        created_incomes = []
        for i, inc_data in enumerate(incomes_data):
            apartment = created_apartments[i % len(created_apartments)]
            
            income = models.Income(
                apartment_id=apartment.id,
                date=(base_date + timedelta(days=i*3)).date(),
                amount_gross=inc_data["amount"],
                currency="EUR",
                status=inc_data["status"],
                source="demo_init"
            )
            db.add(income)
            created_incomes.append(income)
        
        db.commit()
        
        return {
            "success": True,
            "message": "Datos de demostración creados",
            "apartments": len(created_apartments),
            "expenses": len(created_expenses),
            "incomes": len(created_incomes),
            "apartment_codes": [apt.code for apt in created_apartments],
            "next_steps": [
                "1. Ejecuta el bot: python app/bot/Telegram_expense_bot.py",
                "2. En Telegram: /start",
                "3. Configura apartamento: /usar SES01",
                "4. Envía foto de factura",
                "5. Ve el dashboard: /api/v1/dashboard/"
            ]
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@app.post("/bot/setup-webhook")
async def setup_webhook():
    """Configurar webhook de Telegram"""
    try:
        # Usar el endpoint del webhook_bot
        from .webhook_bot import ensure_telegram_app_initialized
        import os
        
        token = os.getenv("TELEGRAM_TOKEN")
        if not token:
            return {"success": False, "error": "TELEGRAM_TOKEN no configurado"}
        
        # Inicializar la aplicación de Telegram si no está inicializada
        app = await ensure_telegram_app_initialized()
        if not app:
            return {"success": False, "error": "No se pudo inicializar el bot"}
        
        webhook_url = f"https://ses-gastos.onrender.com/webhook/telegram"
        
        # Configurar webhook usando la aplicación de Telegram
        success = await app.bot.set_webhook(url=webhook_url)
        
        if success:
            webhook_info = await app.bot.get_webhook_info()
            return {
                "success": True,
                "message": "Webhook configurado correctamente",
                "webhook_url": webhook_url,
                "webhook_info": {
                    "url": webhook_info.url,
                    "pending_updates": webhook_info.pending_update_count
                }
            }
        else:
            return {"success": False, "error": "No se pudo configurar el webhook"}
            
    except Exception as e:
        import traceback
        print(f"Error configurando webhook: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return {"success": False, "error": str(e)}

@app.get("/bot/webhook-status")
async def webhook_status():
    """Verificar estado del webhook de Telegram"""
    try:
        from .webhook_bot import ensure_telegram_app_initialized
        import os
        
        token = os.getenv("TELEGRAM_TOKEN")
        if not token:
            return {"success": False, "error": "TELEGRAM_TOKEN no configurado"}
        
        app = await ensure_telegram_app_initialized()
        if not app:
            return {"success": False, "error": "Bot no inicializado"}
        
        # Obtener información del webhook
        webhook_info = await app.bot.get_webhook_info()
        bot_info = await app.bot.get_me()
        
        return {
            "success": True,
            "bot": {
                "username": bot_info.username,
                "first_name": bot_info.first_name,
                "id": bot_info.id
            },
            "webhook": {
                "url": webhook_info.url,
                "has_custom_certificate": webhook_info.has_custom_certificate,
                "pending_update_count": webhook_info.pending_update_count,
                "last_error_date": webhook_info.last_error_date.isoformat() if webhook_info.last_error_date else None,
                "last_error_message": webhook_info.last_error_message,
                "max_connections": webhook_info.max_connections
            },
            "status": "configured" if webhook_info.url else "not_configured"
        }
    except Exception as e:
        import traceback
        print(f"Error verificando webhook: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return {"success": False, "error": str(e)}

@app.get("/bot/diagnose")
async def diagnose_bot():
    """Diagnóstico completo del bot de Telegram"""
    try:
        import os
        from .webhook_bot import ensure_telegram_app_initialized
        
        diagnosis = {
            "environment": {},
            "initialization": {},
            "webhook": {},
            "recommendations": []
        }
        
        # 1. Verificar variables de entorno
        telegram_token = os.getenv("TELEGRAM_TOKEN")
        openai_key = os.getenv("OPENAI_API_KEY")
        admin_key = os.getenv("ADMIN_KEY") or os.getenv("INTERNAL_KEY")
        api_base_url = os.getenv("API_BASE_URL", "https://ses-gastos.onrender.com")
        
        diagnosis["environment"] = {
            "telegram_token": "✅ Configurado" if telegram_token else "❌ Faltante",
            "openai_key": "✅ Configurado" if openai_key else "❌ Faltante",
            "admin_key": "✅ Configurado" if admin_key else "❌ Faltante",
            "api_base_url": api_base_url,
            "telegram_token_preview": f"...{telegram_token[-4:]}" if telegram_token else None
        }
        
        if not telegram_token:
            diagnosis["recommendations"].append("Configurar TELEGRAM_TOKEN en las variables de entorno")
            return diagnosis
        
        # 2. Probar inicialización
        try:
            app = await ensure_telegram_app_initialized()
            if app:
                diagnosis["initialization"]["status"] = "✅ Exitosa"
                
                # Obtener info del bot
                bot_info = await app.bot.get_me()
                diagnosis["initialization"]["bot_info"] = {
                    "username": bot_info.username,
                    "first_name": bot_info.first_name,
                    "id": bot_info.id
                }
                
                # 3. Verificar webhook
                webhook_info = await app.bot.get_webhook_info()
                diagnosis["webhook"] = {
                    "url": webhook_info.url or "No configurado",
                    "pending_updates": webhook_info.pending_update_count,
                    "last_error_date": webhook_info.last_error_date.isoformat() if webhook_info.last_error_date else None,
                    "last_error_message": webhook_info.last_error_message,
                    "status": "✅ Configurado" if webhook_info.url else "⚠️ No configurado"
                }
                
                # Recomendaciones
                if not webhook_info.url:
                    diagnosis["recommendations"].append("Configurar webhook usando /bot/setup-webhook")
                
                if webhook_info.pending_update_count > 0:
                    diagnosis["recommendations"].append(f"Hay {webhook_info.pending_update_count} updates pendientes")
                
                if webhook_info.last_error_message:
                    diagnosis["recommendations"].append(f"Último error del webhook: {webhook_info.last_error_message}")
                
                if not admin_key:
                    diagnosis["recommendations"].append("Configurar ADMIN_KEY para autenticación de API")
                
            else:
                diagnosis["initialization"]["status"] = "❌ Falló"
                diagnosis["recommendations"].append("La inicialización del bot falló")
                
        except Exception as init_error:
            diagnosis["initialization"]["status"] = f"❌ Error: {str(init_error)}"
            diagnosis["recommendations"].append(f"Error de inicialización: {str(init_error)}")
        
        # Estado general
        if not diagnosis["recommendations"]:
            diagnosis["overall_status"] = "✅ Todo funcionando correctamente"
        else:
            diagnosis["overall_status"] = f"⚠️ {len(diagnosis['recommendations'])} problemas encontrados"
        
        return diagnosis
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
