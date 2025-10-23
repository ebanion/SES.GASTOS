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
    try:
        Base.metadata.create_all(bind=engine)
        print("[startup] DB ready")
    except Exception as e:
        print(f"[startup] create_all failed: {e}")
    
    # Inicializar apartamentos básicos si no existen
    try:
        from .db import SessionLocal
        from . import models
        
        db = SessionLocal()
        existing_apartments = db.query(models.Apartment).count()
        
        if existing_apartments == 0:
            print("[startup] No apartments found, creating default apartments...")
            
            default_apartments = [
                {"code": "SES01", "name": "Apartamento Centro", "owner_email": "admin@sesgas.com"},
                {"code": "SES02", "name": "Apartamento Playa", "owner_email": "admin@sesgas.com"},
                {"code": "SES03", "name": "Apartamento Montaña", "owner_email": "admin@sesgas.com"}
            ]
            
            for apt_data in default_apartments:
                apt = models.Apartment(
                    code=apt_data["code"],
                    name=apt_data["name"],
                    owner_email=apt_data["owner_email"],
                    is_active=True
                )
                db.add(apt)
            
            db.commit()
            print(f"[startup] Created {len(default_apartments)} default apartments")
        else:
            print(f"[startup] Found {existing_apartments} existing apartments")
            
        db.close()
        
    except Exception as e:
        print(f"[startup] Error initializing apartments: {e}")
    
    # Iniciar bot de Telegram
    try:
        from .telegram_bot_service import telegram_service
        if telegram_service.should_start_bot():
            telegram_service.start_bot_in_thread()
            print("[startup] ✅ Telegram bot iniciado correctamente")
        else:
            print("[startup] ⚠️ Telegram bot no iniciado - faltan variables de entorno")
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

@app.get("/db-status")
def db_status():
    """Check database connection status"""
    try:
        from app.db import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"database": "connected", "status": "ok"}
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
