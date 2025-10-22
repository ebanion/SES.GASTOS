# app/webhook_bot.py
"""
Bot de Telegram usando webhooks en lugar de polling
Más adecuado para entornos de producción como Render
"""
import os
import json
import logging
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://ses-gastos.onrender.com/webhook/telegram")
API_BASE_URL = os.getenv("API_BASE_URL", "https://ses-gastos.onrender.com")
INTERNAL_KEY = os.getenv("INTERNAL_KEY") or os.getenv("ADMIN_KEY")

# Router para webhooks
webhook_router = APIRouter(prefix="/webhook", tags=["webhook"])

# Estado global de usuarios
user_sessions: Dict[int, Dict[str, Any]] = {}

# Aplicación de Telegram
telegram_app = None

async def init_telegram_app():
    """Inicializar aplicación de Telegram"""
    global telegram_app
    
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN no configurado")
        return None
    
    telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Agregar handlers
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("usar", usar_apartamento))
    telegram_app.add_handler(CommandHandler("actual", actual))
    telegram_app.add_handler(CommandHandler("reset", reset_apartamento))
    telegram_app.add_handler(CommandHandler("status", status_command))
    telegram_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # IMPORTANTE: Inicializar la aplicación
    await telegram_app.initialize()
    
    logger.info("🤖 Aplicación de Telegram inicializada con webhooks")
    return telegram_app

async def start(update: Update, context):
    """Comando /start"""
    user_name = update.effective_user.first_name or "Usuario"
    await update.message.reply_text(
        f"¡Hola {user_name}! 👋\n\n"
        f"🤖 Bot SES.GASTOS funcionando en producción!\n\n"
        f"📋 **Pasos:**\n"
        f"1️⃣ /usar SES01 (configurar apartamento)\n"
        f"2️⃣ Enviar foto 📸 de factura\n"
        f"3️⃣ Introducir datos manualmente\n"
        f"4️⃣ ¡Gasto registrado automáticamente!\n\n"
        f"🌐 Dashboard: {API_BASE_URL}/api/v1/dashboard/"
    )

async def usar_apartamento(update: Update, context):
    """Comando /usar"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "❌ Especifica el apartamento: /usar SES01\n\n"
            "Disponibles: SES01, SES02, SES03"
        )
        return
    
    apartment_code = context.args[0].upper()
    
    # Verificar apartamento usando httpx asíncrono
    try:
        import httpx
        import asyncio
        
        # Usar httpx asíncrono con timeout más largo
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(f"{API_BASE_URL}/api/v1/apartments/")
            
            if response.status_code == 200:
                apartments = response.json()
                apartment = next((apt for apt in apartments if apt['code'] == apartment_code), None)
                
                if apartment:
                    user_sessions[user_id] = {
                        "apartment_code": apartment_code,
                        "apartment_id": apartment['id']
                    }
                    await update.message.reply_text(
                        f"✅ Apartamento configurado: **{apartment_code}**\n\n"
                        f"Ahora envía una foto de factura 📸"
                    )
                else:
                    codes = [apt['code'] for apt in apartments]
                    await update.message.reply_text(
                        f"❌ Apartamento '{apartment_code}' no encontrado.\n\n"
                        f"Disponibles: {', '.join(codes)}"
                    )
            else:
                await update.message.reply_text(
                    f"❌ Error del servidor: HTTP {response.status_code}\n"
                    f"Intenta de nuevo en unos segundos."
                )
                
    except httpx.TimeoutException:
        await update.message.reply_text(
            f"⏰ Timeout conectando con el servidor.\n"
            f"El servidor puede estar ocupado. Intenta de nuevo."
        )
    except Exception as e:
        logger.error(f"Error en comando /usar: {e}")
        await update.message.reply_text(
            f"❌ Error técnico: {str(e)}\n"
            f"Intenta de nuevo o contacta soporte."
        )

async def actual(update: Update, context):
    """Comando /actual"""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id, {})
    
    if session.get("apartment_code"):
        await update.message.reply_text(f"🏠 Apartamento: **{session['apartment_code']}**")
    else:
        await update.message.reply_text("❌ No configurado. Usa: /usar SES01")

async def reset_apartamento(update: Update, context):
    """Comando /reset"""
    user_id = update.effective_user.id
    user_sessions.pop(user_id, None)
    await update.message.reply_text("🔄 Apartamento resetado. Usa /usar <codigo>")

async def status_command(update: Update, context):
    """Comando /status"""
    try:
        import httpx
        
        # Usar httpx asíncrono con timeout más largo
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(f"{API_BASE_URL}/api/v1/apartments/")
            
            if response.status_code == 200:
                apartments = response.json()
                codes = [apt['code'] for apt in apartments]
                await update.message.reply_text(
                    f"📊 **Sistema Operativo**\n\n"
                    f"✅ API: Funcionando\n"
                    f"✅ Apartamentos: {len(apartments)}\n"
                    f"📋 Códigos: {', '.join(codes)}\n\n"
                    f"🌐 Dashboard: {API_BASE_URL}/api/v1/dashboard/"
                )
            else:
                await update.message.reply_text(
                    f"❌ Error del servidor: HTTP {response.status_code}\n"
                    f"Intenta de nuevo en unos segundos."
                )
                
    except httpx.TimeoutException:
        await update.message.reply_text(
            f"⏰ Timeout conectando con el servidor.\n"
            f"El servidor puede estar ocupado. Intenta de nuevo."
        )
    except Exception as e:
        logger.error(f"Error en comando /status: {e}")
        await update.message.reply_text(f"❌ Error técnico: {str(e)}")

async def handle_photo(update: Update, context):
    """Manejar fotos - modo manual"""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id, {})
    
    if not session.get("apartment_code"):
        await update.message.reply_text("❌ Configura apartamento primero: /usar SES01")
        return
    
    await update.message.reply_text(
        f"📸 **Foto recibida para {session['apartment_code']}**\n\n"
        f"📝 **Introduce los datos manualmente:**\n\n"
        f"**Formato (una línea por dato):**\n"
        f"2025-01-21\n"
        f"45.50\n"
        f"Restaurante El Buen Comer\n"
        f"Restauración\n"
        f"Cena de negocios\n\n"
        f"💡 Copia y pega este formato con tus datos reales."
    )

async def handle_text(update: Update, context):
    """Manejar texto para gastos manuales"""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id, {})
    
    if not session.get("apartment_code"):
        await update.message.reply_text("❌ Configura apartamento: /usar SES01")
        return
    
    text = update.message.text.strip()
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if len(lines) >= 4:
        try:
            expense_data = {
                "apartment_id": session['apartment_id'],
                "date": lines[0],
                "amount_gross": float(lines[1]),
                "vendor": lines[2],
                "category": lines[3],
                "description": lines[4] if len(lines) > 4 else lines[2],
                "currency": "EUR",
                "source": "telegram_webhook_manual"
            }
            
            # Crear gasto usando httpx asíncrono
            import httpx
            
            headers = {"Content-Type": "application/json", "X-Internal-Key": INTERNAL_KEY}
            
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.post(
                    f"{API_BASE_URL}/api/v1/expenses/", 
                    json=expense_data, 
                    headers=headers
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    await update.message.reply_text(
                        f"✅ **¡Gasto registrado!**\n\n"
                        f"📅 {expense_data['date']}\n"
                        f"💰 €{expense_data['amount_gross']}\n"
                        f"🏪 {expense_data['vendor']}\n"
                        f"📂 {expense_data['category']}\n"
                        f"🏠 {session['apartment_code']}\n\n"
                        f"🆔 ID: {result.get('expense_id', 'N/A')}\n\n"
                        f"🌐 Ver en: {API_BASE_URL}/api/v1/dashboard/"
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Error del servidor: HTTP {response.status_code}\n"
                        f"Detalles: {response.text[:200]}\n"
                        f"Intenta de nuevo."
                    )
                    
        except httpx.TimeoutException:
            await update.message.reply_text(
                f"⏰ Timeout creando el gasto.\n"
                f"El servidor puede estar ocupado. Intenta de nuevo."
            )
        except ValueError as e:
            await update.message.reply_text(
                f"❌ Error en el formato de datos.\n"
                f"Asegúrate de usar el formato correcto:\n"
                f"Fecha (YYYY-MM-DD)\n"
                f"Importe (número)\n"
                f"Proveedor\n"
                f"Categoría\n"
                f"Descripción (opcional)"
            )
        except Exception as e:
            logger.error(f"Error creando gasto: {e}")
            await update.message.reply_text(f"❌ Error técnico: {str(e)}")
    else:
        await update.message.reply_text(
            f"📝 **Formato incorrecto**\n\n"
            f"Envía 4-5 líneas:\n"
            f"1. Fecha (YYYY-MM-DD)\n"
            f"2. Importe (45.50)\n"
            f"3. Proveedor\n"
            f"4. Categoría\n"
            f"5. Descripción (opcional)"
        )

@webhook_router.post("/telegram")
async def telegram_webhook(request: Request):
    """Endpoint para recibir webhooks de Telegram"""
    try:
        # Asegurar que la aplicación esté inicializada
        app = await ensure_telegram_app_initialized()
        if not app:
            raise HTTPException(status_code=503, detail="Bot no inicializado - TELEGRAM_TOKEN faltante")
        
        # Obtener datos del webhook
        data = await request.json()
        update = Update.de_json(data, app.bot)
        
        # Procesar update
        await app.process_update(update)
        
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error procesando webhook: {e}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@webhook_router.get("/telegram/info")
async def telegram_info():
    """Información del bot y webhook"""
    try:
        app = await ensure_telegram_app_initialized()
        if not app:
            return {"error": "Bot no inicializado - TELEGRAM_TOKEN faltante"}
        
        bot_info = await app.bot.get_me()
        webhook_info = await app.bot.get_webhook_info()
        
        return {
            "bot": {
                "username": bot_info.username,
                "first_name": bot_info.first_name,
                "id": bot_info.id
            },
            "webhook": {
                "url": webhook_info.url,
                "has_custom_certificate": webhook_info.has_custom_certificate,
                "pending_update_count": webhook_info.pending_update_count
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo info del bot: {e}")
        return {"error": str(e)}

@webhook_router.post("/telegram/setup")
async def setup_telegram_webhook():
    """Configurar webhook de Telegram automáticamente"""
    try:
        app = await ensure_telegram_app_initialized()
        if not app:
            return {"success": False, "error": "Bot no inicializado - TELEGRAM_TOKEN faltante"}
        
        # URL del webhook
        webhook_url = f"{API_BASE_URL}/webhook/telegram"
        
        # Configurar webhook
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
        logger.error(f"Error configurando webhook: {e}")
        return {"success": False, "error": str(e)}

@webhook_router.delete("/telegram/webhook")
async def delete_telegram_webhook():
    """Eliminar webhook de Telegram (volver a polling)"""
    try:
        app = await ensure_telegram_app_initialized()
        if not app:
            return {"success": False, "error": "Bot no inicializado"}
        
        success = await app.bot.delete_webhook()
        return {
            "success": success,
            "message": "Webhook eliminado" if success else "Error eliminando webhook"
        }
    except Exception as e:
        logger.error(f"Error eliminando webhook: {e}")
        return {"success": False, "error": str(e)}

# Inicializar al importar
telegram_app = None
_initialization_task = None

async def ensure_telegram_app_initialized():
    """Asegurar que la aplicación de Telegram esté inicializada"""
    global telegram_app, _initialization_task
    
    if telegram_app is not None:
        return telegram_app
    
    if not TELEGRAM_TOKEN:
        logger.warning("❌ TELEGRAM_TOKEN no configurado - webhook bot deshabilitado")
        return None
    
    # Evitar múltiples inicializaciones concurrentes
    if _initialization_task is None:
        _initialization_task = init_telegram_app()
    
    telegram_app = await _initialization_task
    logger.info("🤖 Bot webhook inicializado")
    return telegram_app