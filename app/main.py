# app/main.py
import os
from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# Importa modelos para que SQLAlchemy “conozca” las tablas
from . import models  # noqa

from .db import Base, engine, get_db

# Importaciones básicas primero - importar individualmente para evitar fallos en cadena
auth = None
apartments = None
incomes = None
reservations = None
expenses = None
admin = None
public = None
user_dashboard = None
email_setup = None
email_webhooks = None
vectors = None
management = None
fix_incomes = None
real_time_api = None

try:
    from .routers import auth
    print("[import] ✅ Auth router importado")
except Exception as e:
    print(f"[import] ❌ Error en auth router: {e}")

try:
    from .routers import auth_multiuser
    print("[import] ✅ Auth multiuser router importado")
except Exception as e:
    print(f"[import] ❌ Error en auth_multiuser router: {e}")

try:
    from .routers import accounts
    print("[import] ✅ Accounts router importado")
except Exception as e:
    print(f"[import] ❌ Error en accounts router: {e}")

try:
    from .routers import multiuser_web
    print("[import] ✅ Multiuser web router importado")
except Exception as e:
    print(f"[import] ❌ Error en multiuser_web router: {e}")

try:
    from .routers import apartments
    print("[import] ✅ Apartments router importado")
except Exception as e:
    print(f"[import] ❌ Error en apartments router: {e}")

try:
    from .routers import incomes
    print("[import] ✅ Incomes router importado")
except Exception as e:
    print(f"[import] ❌ Error en incomes router: {e}")

try:
    from .routers import reservations
    print("[import] ✅ Reservations router importado")
except Exception as e:
    print(f"[import] ❌ Error en reservations router: {e}")

try:
    from .routers import expenses
    print("[import] ✅ Expenses router importado")
except Exception as e:
    print(f"[import] ❌ Error en expenses router: {e}")

try:
    from .routers import admin
    print("[import] ✅ Admin router importado")
except Exception as e:
    print(f"[import] ❌ Error en admin router: {e}")

try:
    from .routers import public
    print("[import] ✅ Public router importado")
except Exception as e:
    print(f"[import] ❌ Error en public router: {e}")

try:
    from .routers import user_dashboard
    print("[import] ✅ User dashboard router importado")
except Exception as e:
    print(f"[import] ❌ Error en user_dashboard router: {e}")

try:
    from .routers import email_setup
    print("[import] ✅ Email setup router importado")
except Exception as e:
    print(f"[import] ❌ Error en email_setup router: {e}")

try:
    from .routers import email_webhooks
    print("[import] ✅ Email webhooks router importado")
except Exception as e:
    print(f"[import] ❌ Error en email_webhooks router: {e}")

try:
    from .routers import vectors
    print("[import] ✅ Vectors router importado")
except Exception as e:
    print(f"[import] ❌ Error en vectors router: {e}")

try:
    from .routers import management
    print("[import] ✅ Management router importado")
except Exception as e:
    print(f"[import] ❌ Error en management router: {e}")

try:
    from .routers import fix_incomes
    print("[import] ✅ Fix incomes router importado")
except Exception as e:
    print(f"[import] ❌ Error en fix_incomes router: {e}")

try:
    from .routers import real_time_api
    print("[import] ✅ Real time API router importado")
except Exception as e:
    print(f"[import] ❌ Error en real_time_api router: {e}")

# Importar admin_management por separado para evitar errores
try:
    from .routers import admin_management
    print("[import] ✅ Admin management importado")
    ADMIN_MANAGEMENT_AVAILABLE = True
except Exception as e:
    print(f"[import] ⚠️ Admin management no disponible: {e}")
    ADMIN_MANAGEMENT_AVAILABLE = False

try:
    from .routers import chat
    print("[import] ✅ Chat integrado importado")
except Exception as e:
    print(f"[import] ❌ Error en chat router: {e}")
    chat = None

try:
    from .dashboard_api import router as dashboard_router
    print("[import] ✅ Dashboard importado")
except Exception as e:
    print(f"[import] ❌ Error en dashboard: {e}")
    dashboard_router = None



app = FastAPI(title="SES.GASTOS")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/debug/database-status")
def database_status():
    """Verificar estado de la base de datos"""
    try:
        from .db import DATABASE_URL, engine
        import os
        
        # Información de la base de datos
        db_info = {
            "database_url": str(engine.url).replace(str(engine.url).split('@')[0].split(':')[-1], "***") if '@' in str(engine.url) else str(engine.url),
            "database_type": "PostgreSQL" if "postgresql" in str(engine.url) else "SQLite",
            "is_temporary": "/tmp/" in str(engine.url),
            "persistence": "❌ TEMPORAL (se pierde en despliegues)" if "/tmp/" in str(engine.url) else "✅ PERSISTENTE"
        }
        
        # Variables de entorno disponibles
        env_vars = {
            "DATABASE_URL": "✅" if os.getenv("DATABASE_URL") else "❌",
            "DATABASE_PRIVATE_URL": "✅" if os.getenv("DATABASE_PRIVATE_URL") else "❌", 
            "POSTGRES_URL": "✅" if os.getenv("POSTGRES_URL") else "❌"
        }
        
        return {
            "success": True,
            "database_info": db_info,
            "environment_variables": env_vars,
            "recommendation": "Configurar PostgreSQL en Render para persistencia" if db_info["is_temporary"] else "Base de datos configurada correctamente"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/debug/create-test-user")
def create_test_user(db: Session = Depends(get_db)):
    """Crear usuario de prueba para testing con SQLite"""
    try:
        
        # Crear cuenta de prueba
        test_account = models.Account(
            name="Cuenta de Prueba",
            slug="prueba",
            description="Cuenta para testing del bot",
            max_apartments=10
        )
        db.add(test_account)
        db.flush()
        
        # Crear usuario de prueba
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        test_user = models.User(
            email="test@sesgas.com",
            full_name="Usuario de Prueba",
            password_hash=pwd_context.hash("test123"),
            is_active=True
        )
        db.add(test_user)
        db.flush()
        
        # Asociar usuario con cuenta
        account_user = models.AccountUser(
            user_id=test_user.id,
            account_id=test_account.id,
            role="owner"
        )
        db.add(account_user)
        
        # Crear apartamento de prueba
        test_apartment = models.Apartment(
            code="TEST01",
            name="Apartamento de Prueba",
            owner_email="test@sesgas.com",
            account_id=test_account.id,
            is_active=True
        )
        db.add(test_apartment)
        
        db.commit()
        
        return {
            "success": True,
            "message": "Usuario de prueba creado",
            "credentials": {
                "email": "test@sesgas.com",
                "password": "test123",
                "apartment_code": "TEST01"
            },
            "instructions": [
                "1. En el bot: /login",
                "2. Email: test@sesgas.com",
                "3. Password: test123",
                "4. /usar TEST01",
                "5. Enviar gasto de prueba"
            ]
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/debug/bot-auth")
def debug_bot_auth():
    """Debug de autenticación del bot"""
    try:
        from sqlalchemy.orm import Session
        db = next(get_db())
        
        # Verificar tablas existentes
        tables_info = {}
        
        # Verificar usuarios
        users_count = db.query(models.User).count()
        users = db.query(models.User).limit(5).all()
        tables_info["users"] = {
            "count": users_count,
            "sample": [{"id": u.id, "email": u.email, "full_name": u.full_name} for u in users]
        }
        
        # Verificar cuentas
        accounts_count = db.query(models.Account).count()
        accounts = db.query(models.Account).limit(5).all()
        tables_info["accounts"] = {
            "count": accounts_count,
            "sample": [{"id": a.id, "name": a.name, "slug": a.slug} for a in accounts]
        }
        
        # Verificar apartamentos
        apartments_count = db.query(models.Apartment).count()
        apartments = db.query(models.Apartment).limit(5).all()
        tables_info["apartments"] = {
            "count": apartments_count,
            "sample": [{"id": a.id, "code": a.code, "name": a.name, "account_id": a.account_id} for a in apartments]
        }
        
        # Verificar relaciones usuario-cuenta
        account_users_count = db.query(models.AccountUser).count()
        account_users = db.query(models.AccountUser).limit(5).all()
        tables_info["account_users"] = {
            "count": account_users_count,
            "sample": [{"user_id": au.user_id, "account_id": au.account_id, "role": au.role} for au in account_users]
        }
        
        return {
            "success": True,
            "database_type": "SQLite" if "sqlite" in str(engine.url) else "PostgreSQL",
            "database_url": str(engine.url).replace(str(engine.url).split('@')[0].split(':')[-1], "***") if '@' in str(engine.url) else str(engine.url),
            "tables": tables_info,
            "instructions": {
                "create_user": "POST /debug/create-test-user",
                "test_login": "POST /api/v1/auth/login with email/password",
                "test_apartments": "GET /api/v1/apartments/ with Authorization header"
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/debug/test-login")
def debug_test_login(credentials: dict):
    """Test login endpoint"""
    try:
        email = credentials.get("email", "test@sesgas.com")
        password = credentials.get("password", "test123")
        
        # Simular login
        import requests
        response = requests.post(
            "https://ses-gastos.onrender.com/api/v1/auth/login",
            json={"email": email, "password": password},
            timeout=10
        )
        
        return {
            "success": True,
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text,
            "headers": dict(response.headers)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# Crear/migrar tablas al arrancar
@app.on_event("startup")
def on_startup() -> None:
    # Intentar reconectar a PostgreSQL si es posible
    global engine
    try:
        database_url = os.getenv("DATABASE_URL")
        if database_url and "postgresql" in database_url:
            print("[startup] 🔄 Intentando reconectar a PostgreSQL...")
            from sqlalchemy import create_engine, text
            
            pg_engine = create_engine(
                database_url, 
                pool_pre_ping=True,
                connect_args={"connect_timeout": 30, "application_name": "ses-gastos"}
            )
            
            # Test de conexión
            with pg_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Si llegamos aquí, PostgreSQL funciona
            engine = pg_engine
            print("[startup] ✅ PostgreSQL reconectado exitosamente")
        else:
            print("[startup] 📁 Continuando con SQLite")
            
    except Exception as pg_error:
        print(f"[startup] ❌ PostgreSQL falló en startup: {pg_error}")
        print("[startup] 📁 Continuando con SQLite")
    
    try:
        Base.metadata.create_all(bind=engine)
        print("[startup] ✅ Tablas creadas/verificadas")
    except Exception as e:
        print(f"[startup] ❌ Error creando tablas: {e}")
    
    # Inicializar apartamentos básicos si no existen
    try:
        from .db import SessionLocal
        from . import models
        
        db = SessionLocal()
        existing_apartments = db.query(models.Apartment).count()
        
        if existing_apartments == 0:
            print("[startup] No apartments found, creating default apartments...")
            
            # Crear cuenta por defecto si no existe
            default_account = db.query(models.Account).filter(models.Account.slug == "sistema").first()
            if not default_account:
                default_account = models.Account(
                    name="Sistema",
                    slug="sistema",
                    description="Cuenta por defecto del sistema",
                    max_apartments=1000
                )
                db.add(default_account)
                db.flush()  # Para obtener el ID
            
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
                    account_id=default_account.id,  # AGREGAR CUENTA
                    is_active=True
                )
                db.add(apt)
                created_apartments.append(apt)
            
            db.commit()
            print(f"[startup] Created {len(default_apartments)} default apartments")
            
            # Crear datos de demostración automáticamente
            try:
                from datetime import date, timedelta
                
                # Crear gastos de demo
                expenses_demo = [
                    {"amount": 45.50, "category": "Restauración", "vendor": "Restaurante Demo", "description": "Cena de negocios"},
                    {"amount": 25.00, "category": "Transporte", "vendor": "Taxi Express", "description": "Traslado aeropuerto"},
                    {"amount": 80.75, "category": "Limpieza", "vendor": "Clean Pro", "description": "Limpieza profunda"},
                    {"amount": 35.00, "category": "Suministros", "vendor": "Ferretería Local", "description": "Material de reparación"}
                ]
                
                for i, exp_data in enumerate(expenses_demo):
                    expense = models.Expense(
                        apartment_id=created_apartments[0].id,  # SES01
                        date=date.today(),
                        amount_gross=exp_data["amount"],
                        currency="EUR",
                        category=exp_data["category"],
                        description=exp_data["description"],
                        vendor=exp_data["vendor"],
                        source="demo_startup"
                    )
                    db.add(expense)
                
                # Crear reservas de demo
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
                
                # Crear ingresos de demo
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
                print(f"[startup] ✅ Datos de demostración creados: {len(expenses_demo)} gastos, 1 reserva, {len(incomes_demo)} ingresos")
                
            except Exception as demo_error:
                print(f"[startup] ⚠️ Error creando datos demo: {demo_error}")
                db.rollback()
        else:
            print(f"[startup] Found {existing_apartments} existing apartments")
            
        db.close()
        
    except Exception as e:
        print(f"[startup] Error initializing apartments: {e}")
    
    # Iniciar bot de Telegram (temporalmente deshabilitado por problemas de threading)
    try:
        # from .telegram_bot_service import telegram_service
        # if telegram_service.should_start_bot():
        #     telegram_service.start_bot_in_thread()
        #     print("[startup] ✅ Telegram bot iniciado correctamente")
        # else:
        #     print("[startup] ⚠️ Telegram bot no iniciado - faltan variables de entorno")
        print("[startup] ⚠️ Bot Telegram deshabilitado temporalmente (usar webhooks)")
    except Exception as e:
        print(f"[startup] ❌ Error iniciando Telegram bot: {e}")

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

@app.get("/debug/test")
def debug_test():
    """Test endpoint para verificar que los endpoints de debug funcionan"""
    return {
        "status": "ok",
        "message": "Debug endpoints funcionando",
        "available_endpoints": [
            "/debug/test",
            "/debug/multitenancy",
            "/debug/multitenancy-page",
            "/fix-multitenancy",
            "/debug/dashboard-apartments"
        ]
    }

@app.get("/debug/dashboard-apartments")
def debug_dashboard_apartments():
    """Debug específico para apartamentos del dashboard"""
    try:
        from .db import SessionLocal
        from . import models
        
        db = SessionLocal()
        try:
            # Obtener TODOS los apartamentos para ver qué hay
            all_apartments = db.query(models.Apartment).all()
            
            apartments_info = []
            for apt in all_apartments:
                apartments_info.append({
                    "id": apt.id,
                    "code": apt.code,
                    "name": apt.name,
                    "owner_email": apt.owner_email,
                    "account_id": apt.account_id,
                    "is_active": apt.is_active,
                    "created_at": str(apt.created_at) if apt.created_at else None
                })
            
            # Obtener cuentas
            accounts = db.query(models.Account).all()
            accounts_info = []
            for account in accounts:
                accounts_info.append({
                    "id": account.id,
                    "name": account.name,
                    "slug": account.slug,
                    "contact_email": account.contact_email,
                    "is_active": account.is_active
                })
            
            return {
                "success": True,
                "total_apartments": len(all_apartments),
                "total_accounts": len(accounts),
                "apartments": apartments_info,
                "accounts": accounts_info,
                "problem_analysis": {
                    "apartments_without_account": len([apt for apt in all_apartments if apt.account_id is None]),
                    "apartments_in_sistema": len([apt for apt in all_apartments if apt.account_id and any(acc.slug == "sistema" and acc.id == apt.account_id for acc in accounts)]),
                    "ses_apartments": [apt for apt in apartments_info if apt["code"] in ["SES01", "SES02", "SES03"]]
                }
            }
            
        finally:
            db.close()
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/test-login")
def test_login():
    """Test simple de login"""
    try:
        from .auth_multiuser import authenticate_user_by_email, get_user_accounts
        from .db import SessionLocal
        
        # Usar credenciales fijas para test
        email = "test@example.com"
        password = "123456"
        
        db = SessionLocal()
        try:
            # Intentar autenticación
            from .auth_multiuser import authenticate_user
            user = authenticate_user(db, email, password)
            
            if user:
                accounts = get_user_accounts(db, user.id)
                return {
                    "success": True,
                    "message": "Login exitoso",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name
                    },
                    "accounts_count": len(accounts)
                }
            else:
                return {
                    "success": False,
                    "message": "Credenciales incorrectas"
                }
                
        finally:
            db.close()
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error en login test"
        }

@app.post("/test-register")
def test_register():
    """Test simple de registro sin autenticación"""
    try:
        from .db import SessionLocal, engine, Base
        from .models import User, Account, AccountUser
        from .auth_multiuser import get_password_hash, create_account_slug, ensure_unique_slug
        from datetime import datetime, timezone, timedelta
        
        # Crear tablas si no existen
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        try:
            # Crear usuario de prueba
            test_user = User(
                email="test@example.com",
                full_name="Usuario Test",
                password_hash=get_password_hash("123456"),
                is_active=True
            )
            db.add(test_user)
            db.flush()
            
            # Crear cuenta de prueba
            test_account = Account(
                name="Cuenta Test",
                slug="test-account",
                contact_email="test@example.com",
                max_apartments=10,
                trial_ends_at=datetime.now(timezone.utc) + timedelta(days=30)
            )
            db.add(test_account)
            db.flush()
            
            # Crear membresía
            membership = AccountUser(
                account_id=test_account.id,
                user_id=test_user.id,
                role="owner",
                invitation_accepted_at=datetime.now(timezone.utc)
            )
            db.add(membership)
            db.commit()
            
            return {
                "success": True,
                "message": "Usuario test creado exitosamente",
                "user_id": test_user.id,
                "account_id": test_account.id,
                "credentials": {
                    "email": "test@example.com",
                    "password": "123456"
                }
            }
            
        finally:
            db.close()
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error creando usuario test"
        }

@app.get("/postgres-debug")
def postgres_debug():
    """Diagnosticar problema de PostgreSQL"""
    import os
    
    # Obtener todas las variables de PostgreSQL
    env_vars = {}
    for key in os.environ:
        if any(word in key.upper() for word in ['DATABASE', 'POSTGRES', 'DB']):
            # Enmascarar contraseñas
            value = os.environ[key]
            if '://' in value and '@' in value:
                # Es una URL de conexión, enmascarar contraseña
                parts = value.split('@')
                if len(parts) > 1:
                    user_pass = parts[0].split('://')[-1]
                    if ':' in user_pass:
                        user, password = user_pass.split(':', 1)
                        masked_value = value.replace(f":{password}@", ":***@")
                        env_vars[key] = masked_value
                    else:
                        env_vars[key] = value
                else:
                    env_vars[key] = value
            else:
                env_vars[key] = value[:10] + "***" if len(value) > 10 else value
    
    # Intentar diferentes URLs de PostgreSQL
    test_results = {}
    
    for var_name, url in env_vars.items():
        if '://' in str(url) and 'postgresql' in str(url).lower():
            try:
                from sqlalchemy import create_engine, text
                test_engine = create_engine(url, pool_pre_ping=True)
                with test_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                test_results[var_name] = "✅ FUNCIONA"
            except Exception as e:
                test_results[var_name] = f"❌ {str(e)[:100]}"
    
    return {
        "environment_variables": env_vars,
        "connection_tests": test_results,
        "current_database": "sqlite" if "sqlite" in str(os.getenv("DATABASE_URL", "")) else "postgresql",
        "recommendation": "Verificar credenciales de PostgreSQL en Render dashboard"
    }

@app.get("/system-status")
def system_status():
    """Diagnóstico completo del sistema"""
    try:
        from .db import engine, DATABASE_URL
        from sqlalchemy import text
        import os
        
        # Test de base de datos
        db_status = "unknown"
        db_type = "unknown"
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_status = "connected"
            db_type = "postgresql" if "postgresql" in DATABASE_URL else "sqlite"
        except Exception as e:
            db_status = f"error: {str(e)[:100]}"
        
        # Test de imports multiusuario
        multiuser_imports = {}
        try:
            import jwt
            multiuser_imports["jwt"] = "✅ OK"
        except ImportError as e:
            multiuser_imports["jwt"] = f"❌ {str(e)}"
        
        try:
            from .auth_multiuser import get_current_user
            multiuser_imports["auth_multiuser"] = "✅ OK"
        except ImportError as e:
            multiuser_imports["auth_multiuser"] = f"❌ {str(e)}"
        
        try:
            from .routers.accounts import router as accounts_router
            multiuser_imports["accounts_router"] = "✅ OK"
        except ImportError as e:
            multiuser_imports["accounts_router"] = f"❌ {str(e)}"
        
        return {
            "system": "SES.GASTOS Multiuser",
            "database": {
                "status": db_status,
                "type": db_type,
                "url_masked": DATABASE_URL.replace(DATABASE_URL.split('@')[0].split(':')[-1], '***') if '@' in DATABASE_URL else DATABASE_URL
            },
            "multiuser_system": multiuser_imports,
            "environment": {
                "DATABASE_URL": "SET" if os.getenv("DATABASE_URL") else "NOT_SET",
                "TELEGRAM_TOKEN": "SET" if os.getenv("TELEGRAM_TOKEN") else "NOT_SET",
                "OPENAI_API_KEY": "SET" if os.getenv("OPENAI_API_KEY") else "NOT_SET"
            },
            "available_endpoints": {
                "multiuser_login": "/multiuser/login",
                "multiuser_register": "/multiuser/register",
                "migration_status": "/migrate/status",
                "superadmin": "/multiuser/superadmin"
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "system": "SES.GASTOS Multiuser",
            "status": "error"
        }

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

@app.post("/fix-postgres-now")
def fix_postgres_now():
    """Arreglar PostgreSQL probando todas las URLs disponibles"""
    import os
    from sqlalchemy import create_engine, text
    
    # Obtener todas las posibles URLs de PostgreSQL
    env_vars = {
        "DATABASE_URL": os.getenv("DATABASE_URL"),
        "DATABASE_PRIVATE_URL": os.getenv("DATABASE_PRIVATE_URL"),
        "POSTGRES_URL": os.getenv("POSTGRES_URL"),
        "POSTGRESQL_URL": os.getenv("POSTGRESQL_URL")
    }
    
    results = []
    working_url = None
    
    for var_name, url in env_vars.items():
        if not url:
            results.append(f"{var_name}: ❌ No configurada")
            continue
            
        if "postgresql" not in url and "postgres" not in url:
            results.append(f"{var_name}: ❌ No es PostgreSQL")
            continue
            
        try:
            # Normalizar URL para psycopg
            test_url = url
            if test_url.startswith("postgres://"):
                test_url = test_url.replace("postgres://", "postgresql+psycopg://", 1)
            elif test_url.startswith("postgresql://"):
                test_url = test_url.replace("postgresql://", "postgresql+psycopg://", 1)
            elif not test_url.startswith("postgresql+psycopg://"):
                test_url = "postgresql+psycopg://" + test_url.split("://", 1)[1]
            
            # Probar conexión
            test_engine = create_engine(
                test_url, 
                pool_pre_ping=True,
                connect_args={"connect_timeout": 10}
            )
            
            with test_engine.connect() as conn:
                version = conn.execute(text("SELECT version()")).scalar()
                db_name = conn.execute(text("SELECT current_database()")).scalar()
                
            results.append(f"{var_name}: ✅ FUNCIONA - DB: {db_name}")
            working_url = test_url
            working_var = var_name
            
            # Actualizar engine global
            global engine
            from sqlalchemy.orm import sessionmaker
            import app.db
            
            engine = test_engine
            app.db.engine = test_engine
            app.db.DATABASE_URL = test_url
            app.db.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
            
            # Crear tablas si no existen
            from app.db import Base
            from app import models
            Base.metadata.create_all(bind=test_engine)
            
            return {
                "success": True,
                "message": f"✅ PostgreSQL reconectado exitosamente usando {working_var}",
                "database": db_name,
                "postgres_version": version.split()[1] if version else "Unknown",
                "working_url_var": working_var,
                "working_url": test_url.replace(test_url.split('@')[0].split(':')[-1], '***'),
                "all_results": results,
                "tables_created": "✅ Tablas verificadas/creadas"
            }
            
        except Exception as e:
            error_msg = str(e)
            if "password authentication failed" in error_msg:
                results.append(f"{var_name}: ❌ Credenciales incorrectas")
            elif "connection" in error_msg.lower():
                results.append(f"{var_name}: ❌ Error de conexión")
            else:
                results.append(f"{var_name}: ❌ {error_msg[:50]}...")
    
    return {
        "success": False,
        "message": "❌ No se pudo conectar con ninguna URL de PostgreSQL",
        "all_results": results,
        "current_fallback": "SQLite en /tmp/ses_gastos.db",
        "suggestion": "Verificar credenciales de PostgreSQL en Render dashboard o usar SQLite temporalmente"
    }

@app.post("/migrate-sqlite-to-postgres")
def migrate_sqlite_to_postgres():
    """Migrar datos de SQLite a PostgreSQL una vez reconectado"""
    try:
        from app.db import engine, DATABASE_URL
        from sqlalchemy import text
        
        # Verificar que estamos usando PostgreSQL
        if "postgresql" not in DATABASE_URL:
            return {
                "success": False,
                "message": "❌ No estás conectado a PostgreSQL",
                "current_db": DATABASE_URL,
                "suggestion": "Ejecuta /fix-postgres-now primero"
            }
        
        # Contar registros actuales en PostgreSQL
        with engine.connect() as conn:
            apartments_count = conn.execute(text("SELECT COUNT(*) FROM apartments")).scalar()
            expenses_count = conn.execute(text("SELECT COUNT(*) FROM expenses")).scalar()
            incomes_count = conn.execute(text("SELECT COUNT(*) FROM incomes")).scalar()
            
        return {
            "success": True,
            "message": "✅ Ya estás usando PostgreSQL",
            "database": "PostgreSQL",
            "current_data": {
                "apartments": apartments_count,
                "expenses": expenses_count, 
                "incomes": incomes_count
            },
            "note": "Los datos ya están en PostgreSQL"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "❌ Error verificando migración"
        }

@app.get("/")
def root():
    return {
        "message": "🏠 SES.GASTOS - Sistema de Gestión de Gastos",
        "status": "active",
        "multiuser": {
            "login": "/multiuser/login",
            "register": "/multiuser/register",
            "superadmin": "/multiuser/superadmin"
        },
        "legacy": {
            "auth": "/auth/",
            "dashboard": "/dashboard/"
        },
        "health": "/health",
        "migration": "/migrate/status"
    }

@app.get("/dashboard")
def dashboard_redirect():
    return RedirectResponse(url="/api/v1/dashboard/")

# Incluir routers básicos solamente - verificar que estén importados
if auth:
    try:
        app.include_router(auth.router)
        print("[router] ✅ Auth router incluido")
    except Exception as e:
        print(f"[router] ❌ Error incluyendo auth: {e}")

# Incluir nuevos routers multiusuario
try:
    if 'auth_multiuser' in locals():
        app.include_router(auth_multiuser.router)
        print("[router] ✅ Auth multiuser router incluido")
except Exception as e:
    print(f"[router] ❌ Error incluyendo auth_multiuser: {e}")

try:
    if 'accounts' in locals():
        app.include_router(accounts.router)
        print("[router] ✅ Accounts router incluido")
except Exception as e:
    print(f"[router] ❌ Error incluyendo accounts: {e}")

try:
    if 'multiuser_web' in locals():
        app.include_router(multiuser_web.router)
        print("[router] ✅ Multiuser web router incluido")
except Exception as e:
    print(f"[router] ❌ Error incluyendo multiuser_web: {e}")

if apartments:
    try:
        app.include_router(apartments.router)
        print("[router] ✅ Apartments router incluido")
    except Exception as e:
        print(f"[router] ❌ Error incluyendo apartments: {e}")

if incomes:
    try:
        app.include_router(incomes.router)
        print("[router] ✅ Incomes router incluido")
    except Exception as e:
        print(f"[router] ❌ Error incluyendo incomes: {e}")

if reservations:
    try:
        app.include_router(reservations.router)
        print("[router] ✅ Reservations router incluido")
    except Exception as e:
        print(f"[router] ❌ Error incluyendo reservations: {e}")

if expenses:
    try:
        app.include_router(expenses.router)
        print("[router] ✅ Expenses router incluido")
    except Exception as e:
        print(f"[router] ❌ Error incluyendo expenses: {e}")

if admin:
    try:
        app.include_router(admin.router)
        print("[router] ✅ Admin router incluido")
    except Exception as e:
        print(f"[router] ❌ Error incluyendo admin: {e}")

if public:
    try:
        app.include_router(public.router)
        print("[router] ✅ Public router incluido")
    except Exception as e:
        print(f"[router] ❌ Error incluyendo public: {e}")

if user_dashboard:
    try:
        app.include_router(user_dashboard.router)
        print("[router] ✅ User dashboard router incluido")
    except Exception as e:
        print(f"[router] ❌ Error incluyendo user_dashboard: {e}")

if email_setup:
    try:
        app.include_router(email_setup.router)
        print("[router] ✅ Email setup router incluido")
    except Exception as e:
        print(f"[router] ❌ Error incluyendo email_setup: {e}")

if email_webhooks:
    try:
        app.include_router(email_webhooks.router)
        print("[router] ✅ Email webhooks router incluido")
    except Exception as e:
        print(f"[router] ❌ Error incluyendo email_webhooks: {e}")

if vectors:
    try:
        app.include_router(vectors.router)
        print("[router] ✅ Vectors router incluido")
    except Exception as e:
        print(f"[router] ❌ Error incluyendo vectors: {e}")

if management:
    try:
        app.include_router(management.router)
        print("[router] ✅ Management router incluido")
    except Exception as e:
        print(f"[router] ❌ Error incluyendo management: {e}")

if fix_incomes:
    try:
        app.include_router(fix_incomes.router)
        print("[router] ✅ Fix incomes router incluido")
    except Exception as e:
        print(f"[router] ❌ Error incluyendo fix_incomes: {e}")

if real_time_api:
    try:
        app.include_router(real_time_api.router)
        print("[router] ✅ Real time API router incluido")
    except Exception as e:
        print(f"[router] ❌ Error incluyendo real_time_api: {e}")

if ADMIN_MANAGEMENT_AVAILABLE:
    try:
        app.include_router(admin_management.router)
        print("[router] ✅ Admin management router incluido")
    except Exception as e:
        print(f"[router] ❌ Error incluyendo admin_management: {e}")
else:
    print("[router] ⚠️ Admin management no disponible")

# Agregar webhook de Telegram para producción
try:
    from .webhook_bot import webhook_router
    app.include_router(webhook_router)
    print("[router] ✅ Telegram webhook router incluido")
except Exception as e:
    print(f"[router] ❌ Error incluyendo telegram webhook: {e}")

if chat:
    try:
        app.include_router(chat.router)
        print("[router] ✅ Chat integrado router incluido")
    except Exception as e:
        print(f"[router] ❌ Error incluyendo chat: {e}")

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

@app.post("/fix-postgres-connection")
def fix_postgres_connection():
    """Intentar reconectar a PostgreSQL con credenciales actualizadas"""
    import os
    from sqlalchemy import create_engine, text
    
    # Obtener todas las posibles URLs de PostgreSQL
    database_urls = [
        os.getenv("DATABASE_URL"),
        os.getenv("DATABASE_PRIVATE_URL"), 
        os.getenv("POSTGRES_URL"),
        os.getenv("POSTGRESQL_URL")
    ]
    
    results = []
    
    for i, url in enumerate(database_urls):
        if not url:
            results.append(f"URL {i+1}: No configurada")
            continue
            
        if "postgresql" not in url:
            results.append(f"URL {i+1}: No es PostgreSQL")
            continue
            
        try:
            # Normalizar URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg://", 1)
            elif not url.startswith("postgresql+psycopg://"):
                url = url.replace("postgresql://", "postgresql+psycopg://", 1)
            
            # Probar conexión
            test_engine = create_engine(url, pool_pre_ping=True)
            with test_engine.connect() as conn:
                version = conn.execute(text("SELECT version()")).scalar()
                db_name = conn.execute(text("SELECT current_database()")).scalar()
                
            results.append(f"URL {i+1}: ✅ FUNCIONA - DB: {db_name}")
            
            # Si funciona, actualizar engine global
            global engine
            from sqlalchemy.orm import sessionmaker
            engine = test_engine
            app.db.engine = test_engine
            app.db.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
            
            return {
                "success": True,
                "message": f"✅ PostgreSQL reconectado exitosamente",
                "database": db_name,
                "postgres_version": version.split()[1],
                "url_used": f"URL {i+1}",
                "all_results": results
            }
            
        except Exception as e:
            results.append(f"URL {i+1}: ❌ Error - {str(e)[:100]}")
    
    return {
        "success": False,
        "message": "❌ No se pudo conectar con ninguna URL de PostgreSQL",
        "all_results": results,
        "suggestion": "Verificar credenciales de PostgreSQL en Render dashboard"
    }

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

# ---------- ENDPOINTS DE MIGRACIÓN MULTIUSUARIO ----------

@app.post("/migrate/to-multiuser")
def migrate_to_multiuser():
    """Migrar datos existentes al sistema multiusuario"""
    try:
        from .migration_multiuser import migrate_to_multiuser_system
        from .db import SessionLocal
        
        db = SessionLocal()
        try:
            result = migrate_to_multiuser_system(db)
            return result
        finally:
            db.close()
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error en migración multiusuario"
        }

@app.post("/migrate/render-fix-now")
def migrate_render_fix_now():
    """Migración URGENTE para Render - Arregla aislamiento de apartamentos"""
    import os
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return {"success": False, "error": "DATABASE_URL no configurada"}
    
    try:
        # Usar engine existente de la aplicación
        from .db import engine
        from sqlalchemy import text
        
        migrations = []
        
        with engine.connect() as conn:
            # Migración crítica: agregar account_id a apartments
            try:
                conn.execute(text("ALTER TABLE apartments ADD COLUMN IF NOT EXISTS account_id VARCHAR(36)"))
                migrations.append("✅ Columna account_id agregada a apartments")
            except Exception as e:
                migrations.append(f"⚠️ account_id: {str(e)[:50]}")
            
            # Crear tabla accounts básica
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS accounts (
                        id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
                        name VARCHAR(255) NOT NULL,
                        slug VARCHAR(100) UNIQUE NOT NULL,
                        description VARCHAR(500),
                        is_active BOOLEAN DEFAULT TRUE,
                        max_apartments INTEGER DEFAULT 10,
                        contact_email VARCHAR(255),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """))
                migrations.append("✅ Tabla accounts creada")
            except Exception as e:
                migrations.append(f"⚠️ Tabla accounts: {str(e)[:50]}")
            
            # Crear cuenta sistema
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM accounts WHERE slug = 'sistema'")).scalar()
                if result == 0:
                    conn.execute(text("""
                        INSERT INTO accounts (name, slug, description, max_apartments, is_active)
                        VALUES ('Sistema', 'sistema', 'Cuenta demo - apartamentos SES01, SES02, SES03', 1000, true)
                    """))
                    migrations.append("✅ Cuenta 'Sistema' creada para apartamentos demo")
                else:
                    migrations.append("✅ Cuenta 'Sistema' ya existe")
            except Exception as e:
                migrations.append(f"⚠️ Cuenta sistema: {str(e)[:50]}")
            
            # CRÍTICO: Asignar apartamentos SES01, SES02, SES03 a cuenta sistema
            try:
                account_id = conn.execute(text("SELECT id FROM accounts WHERE slug = 'sistema'")).scalar()
                if account_id:
                    result = conn.execute(text("""
                        UPDATE apartments 
                        SET account_id = :account_id 
                        WHERE code IN ('SES01', 'SES02', 'SES03') AND account_id IS NULL
                    """), {"account_id": account_id})
                    
                    migrations.append(f"✅ {result.rowcount} apartamentos demo asignados a cuenta Sistema")
                    migrations.append("🎯 AISLAMIENTO ACTIVADO: SES01, SES02, SES03 ahora están en cuenta separada")
                else:
                    migrations.append("❌ No se pudo obtener ID de cuenta sistema")
            except Exception as e:
                migrations.append(f"❌ Error asignando apartamentos: {str(e)[:50]}")
            
            conn.commit()
        
        return {
            "success": True,
            "message": "🎉 AISLAMIENTO DE APARTAMENTOS ACTIVADO",
            "migrations": migrations,
            "result": "Los apartamentos SES01, SES02, SES03 están ahora en cuenta 'Sistema' separada",
            "next_step": "Los nuevos usuarios solo verán sus propios apartamentos"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "❌ Error en migración urgente"
        }

@app.post("/migrate/render-fix")
def migrate_render_fix():
    """Migración específica para Render - Arregla estructura PostgreSQL"""
    import os
    from sqlalchemy import create_engine, text
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return {"success": False, "error": "DATABASE_URL no configurada"}
    
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        
        migrations = []
        
        with engine.connect() as conn:
            # Lista de migraciones críticas
            migration_queries = [
                "ALTER TABLE apartments ADD COLUMN IF NOT EXISTS description VARCHAR(500)",
                "ALTER TABLE apartments ADD COLUMN IF NOT EXISTS address VARCHAR(500)", 
                "ALTER TABLE apartments ADD COLUMN IF NOT EXISTS max_guests INTEGER",
                "ALTER TABLE apartments ADD COLUMN IF NOT EXISTS bedrooms INTEGER",
                "ALTER TABLE apartments ADD COLUMN IF NOT EXISTS bathrooms INTEGER",
                "ALTER TABLE apartments ADD COLUMN IF NOT EXISTS account_id VARCHAR(36)",
                "ALTER TABLE apartments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE",
                
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_superadmin BOOLEAN DEFAULT FALSE",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(50)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'Europe/Madrid'",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(5) DEFAULT 'es'",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE",
            ]
            
            for query in migration_queries:
                try:
                    conn.execute(text(query))
                    migrations.append(f"✅ {query[:50]}...")
                except Exception as e:
                    migrations.append(f"⚠️ {query[:50]}... -> {str(e)[:50]}")
            
            # Crear tabla accounts
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS accounts (
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
                    )
                """))
                migrations.append("✅ Tabla accounts creada")
            except Exception as e:
                migrations.append(f"⚠️ Tabla accounts: {str(e)[:50]}")
            
            # Crear tabla account_users
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS account_users (
                        id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
                        account_id VARCHAR(36) NOT NULL,
                        user_id VARCHAR(36) NOT NULL,
                        role VARCHAR(20) NOT NULL DEFAULT 'member',
                        is_active BOOLEAN DEFAULT TRUE,
                        invited_by VARCHAR(36),
                        invitation_accepted_at TIMESTAMP WITH TIME ZONE,
                        permissions JSON,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE
                    )
                """))
                migrations.append("✅ Tabla account_users creada")
            except Exception as e:
                migrations.append(f"⚠️ Tabla account_users: {str(e)[:50]}")
            
            conn.commit()
            
            # Crear cuenta sistema si no existe
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM accounts WHERE slug = 'sistema'")).scalar()
                if result == 0:
                    conn.execute(text("""
                        INSERT INTO accounts (name, slug, description, max_apartments, is_active)
                        VALUES ('Sistema', 'sistema', 'Cuenta por defecto para apartamentos demo', 1000, true)
                    """))
                    migrations.append("✅ Cuenta 'Sistema' creada")
                else:
                    migrations.append("✅ Cuenta 'Sistema' ya existe")
                
                # Asignar apartamentos sin cuenta
                account_id = conn.execute(text("SELECT id FROM accounts WHERE slug = 'sistema'")).scalar()
                result = conn.execute(text("""
                    UPDATE apartments 
                    SET account_id = :account_id 
                    WHERE account_id IS NULL
                """), {"account_id": account_id})
                
                migrations.append(f"✅ {result.rowcount} apartamentos asignados a cuenta sistema")
                
                conn.commit()
                
            except Exception as e:
                migrations.append(f"⚠️ Error creando cuenta sistema: {str(e)[:50]}")
        
        return {
            "success": True,
            "message": "✅ Migración de Render completada",
            "migrations": migrations,
            "next_step": "El sistema multiusuario está listo"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "❌ Error en migración de Render"
        }

@app.get("/migrate/status")
def get_migration_status():
    """Obtener estado de la migración multiusuario"""
    try:
        from .migration_multiuser import get_migration_status
        from .db import SessionLocal
        
        db = SessionLocal()
        try:
            result = get_migration_status(db)
            return result
        finally:
            db.close()
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/migrate/create-superadmin")
def create_superadmin(
    email: str = "admin@sesgas.com",
    password: str = "admin123",
    full_name: str = "Administrador Sistema"
):
    """Crear usuario superadministrador"""
    try:
        from .migration_multiuser import create_superadmin_user
        from .db import SessionLocal
        
        db = SessionLocal()
        try:
            result = create_superadmin_user(db, email, password, full_name)
            return result
        finally:
            db.close()
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/quick-setup")
def quick_setup():
    """Setup rápido del sistema multiusuario (solo para SQLite)"""
    try:
        from .db import SessionLocal, engine, Base
        from .models import User, Account, AccountUser
        from .auth_multiuser import get_password_hash, create_account_slug, ensure_unique_slug
        from datetime import datetime, timezone, timedelta
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        try:
            # Verificar si ya existe superadmin
            existing_admin = db.query(User).filter(User.is_superadmin == True).first()
            if existing_admin:
                return {
                    "success": True,
                    "message": "Sistema ya configurado",
                    "admin_email": existing_admin.email
                }
            
            # Crear superadmin
            admin_user = User(
                email="admin@sesgas.com",
                full_name="Administrador Sistema",
                password_hash=get_password_hash("admin123"),
                is_active=True,
                is_superadmin=True
            )
            db.add(admin_user)
            db.flush()
            
            # Crear cuenta demo
            demo_account = Account(
                name="Cuenta Demo",
                slug="demo",
                contact_email="demo@sesgas.com",
                description="Cuenta de demostración del sistema",
                max_apartments=50,
                trial_ends_at=datetime.now(timezone.utc) + timedelta(days=30)
            )
            db.add(demo_account)
            db.flush()
            
            # Crear usuario demo
            demo_user = User(
                email="demo@sesgas.com",
                full_name="Usuario Demo",
                password_hash=get_password_hash("demo123"),
                is_active=True,
                is_superadmin=False
            )
            db.add(demo_user)
            db.flush()
            
            # Crear membresía demo
            demo_membership = AccountUser(
                account_id=demo_account.id,
                user_id=demo_user.id,
                role="owner",
                invitation_accepted_at=datetime.now(timezone.utc)
            )
            db.add(demo_membership)
            
            db.commit()
            
            return {
                "success": True,
                "message": "✅ Sistema configurado exitosamente",
                "credentials": {
                    "superadmin": {"email": "admin@sesgas.com", "password": "admin123"},
                    "demo_user": {"email": "demo@sesgas.com", "password": "demo123"}
                },
                "next_steps": [
                    "1. Ir a /multiuser/login",
                    "2. Usar credenciales de superadmin o demo",
                    "3. Probar el sistema multiusuario"
                ]
            }
            
        finally:
            db.close()
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error en configuración rápida"
        }

@app.get("/debug/multitenancy-page", response_class=HTMLResponse)
async def debug_multitenancy_page():
    """Página de debugging para multitenancy"""
    try:
        with open("debug_multitenancy.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Debug multitenancy page not found</h1>", status_code=404)

@app.get("/debug/multitenancy")
async def debug_multitenancy():
    """Diagnosticar problemas de multitenancy"""
    try:
        from .db import SessionLocal
        from . import models
        
        db = SessionLocal()
        try:
            # 1. Estructura de cuentas
            accounts = db.query(models.Account).all()
            accounts_info = []
            
            for account in accounts:
                users_count = db.query(models.AccountUser).filter(models.AccountUser.account_id == account.id).count()
                apartments = db.query(models.Apartment).filter(models.Apartment.account_id == account.id).all()
                
                accounts_info.append({
                    "id": account.id,
                    "name": account.name,
                    "slug": account.slug,
                    "contact_email": account.contact_email,
                    "is_active": account.is_active,
                    "users_count": users_count,
                    "apartments_count": len(apartments),
                    "apartments": [{"code": apt.code, "name": apt.name, "owner_email": apt.owner_email} for apt in apartments]
                })
            
            # 2. Apartamentos legacy (sin cuenta)
            legacy_apartments = db.query(models.Apartment).filter(models.Apartment.account_id == None).all()
            legacy_info = [{"code": apt.code, "name": apt.name, "owner_email": apt.owner_email} for apt in legacy_apartments]
            
            # 3. Usuarios
            users = db.query(models.User).all()
            users_info = []
            
            for user in users:
                memberships = db.query(models.AccountUser).filter(models.AccountUser.user_id == user.id).all()
                user_accounts = []
                
                for membership in memberships:
                    account = db.query(models.Account).filter(models.Account.id == membership.account_id).first()
                    user_accounts.append({
                        "account_name": account.name if account else "Cuenta eliminada",
                        "role": membership.role
                    })
                
                users_info.append({
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_superadmin": user.is_superadmin,
                    "accounts": user_accounts
                })
            
            # 4. Detectar problemas
            problems = []
            if legacy_apartments:
                problems.append(f"❌ {len(legacy_apartments)} apartamentos sin cuenta (legacy)")
            
            return {
                "success": True,
                "accounts": accounts_info,
                "legacy_apartments": legacy_info,
                "users": users_info,
                "problems": problems,
                "summary": {
                    "total_accounts": len(accounts),
                    "total_legacy_apartments": len(legacy_apartments),
                    "total_users": len(users),
                    "problems_count": len(problems)
                }
            }
            
        finally:
            db.close()
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/fix-multitenancy")
async def fix_multitenancy():
    """Arreglar problemas de multitenancy automáticamente"""
    try:
        from .db import SessionLocal
        from . import models
        from .auth_multiuser import create_account_slug, ensure_unique_slug, get_password_hash
        from datetime import datetime, timezone
        
        db = SessionLocal()
        try:
            results = []
            
            # Migrar apartamentos legacy
            legacy_apartments = db.query(models.Apartment).filter(models.Apartment.account_id == None).all()
            
            for apt in legacy_apartments:
                if apt.owner_email:
                    # Buscar o crear cuenta para este email
                    account = db.query(models.Account).filter(models.Account.contact_email == apt.owner_email).first()
                    
                    if not account:
                        # Crear cuenta nueva
                        account_name = f"Cuenta de {apt.owner_email.split('@')[0].title()}"
                        base_slug = create_account_slug(account_name)
                        unique_slug = ensure_unique_slug(db, base_slug)
                        
                        account = models.Account(
                            name=account_name,
                            slug=unique_slug,
                            contact_email=apt.owner_email,
                            max_apartments=50,
                            is_active=True
                        )
                        db.add(account)
                        db.flush()
                        
                        results.append(f"✅ Cuenta creada: {account.name}")
                        
                        # Buscar o crear usuario
                        user = db.query(models.User).filter(models.User.email == apt.owner_email).first()
                        if not user:
                            user = models.User(
                                email=apt.owner_email,
                                full_name=f"Usuario {apt.owner_email.split('@')[0].title()}",
                                password_hash=get_password_hash("123456"),
                                is_active=True
                            )
                            db.add(user)
                            db.flush()
                            
                            results.append(f"✅ Usuario creado: {user.email}")
                        
                        # Crear membresía
                        membership = models.AccountUser(
                            account_id=account.id,
                            user_id=user.id,
                            role="owner",
                            invitation_accepted_at=datetime.now(timezone.utc)
                        )
                        db.add(membership)
                    
                    # Migrar apartamento
                    apt.account_id = account.id
                    results.append(f"🏠 Apartamento migrado: {apt.code} → {account.name}")
            
            db.commit()
            
            return {
                "success": True,
                "message": "✅ Multitenancy arreglado exitosamente",
                "results": results,
                "migrated_apartments": len(legacy_apartments)
            }
            
        finally:
            db.close()
            
    except Exception as e:
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
