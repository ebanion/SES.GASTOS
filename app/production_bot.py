# app/production_bot.py
"""
Bot de Telegram optimizado para producción en Render
Sin dependencias problemáticas como Tesseract
"""
import os
import json
import logging
import tempfile
import asyncio
from pathlib import Path
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuración
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://ses-gastos.onrender.com")
INTERNAL_KEY = os.getenv("INTERNAL_KEY") or os.getenv("ADMIN_KEY")

# Estado por usuario (en memoria para producción)
user_sessions = {}

def save_user_session(user_id: int, data: dict):
    """Guardar sesión de usuario"""
    user_sessions[user_id] = data

def get_user_session(user_id: int) -> dict:
    """Obtener sesión de usuario"""
    return user_sessions.get(user_id, {})

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user_name = update.effective_user.first_name or "Usuario"
    await update.message.reply_text(
        f"¡Hola {user_name}! 👋\n\n"
        f"🤖 Soy el bot de SES.GASTOS en producción!\n\n"
        f"📋 **Pasos para empezar:**\n"
        f"1️⃣ Configura tu apartamento: /usar SES01\n"
        f"2️⃣ Envía una foto 📸 de tu factura\n"
        f"3️⃣ ¡El gasto se registra automáticamente!\n\n"
        f"🔧 **Comandos útiles:**\n"
        f"• /actual - Ver apartamento configurado\n"
        f"• /reset - Cambiar de apartamento\n"
        f"• /status - Estado del sistema\n\n"
        f"💡 **Tip:** Las fotos deben ser claras y legibles."
    )

async def usar_apartamento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /usar <codigo>"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "❌ Debes especificar el código del apartamento.\n\n"
            "Ejemplo: /usar SES01\n\n"
            "Apartamentos disponibles: SES01, SES02, SES03"
        )
        return
    
    apartment_code = context.args[0].upper().strip()
    
    # Verificar que el apartamento existe
    try:
        import requests
        response = requests.get(f"{API_BASE_URL}/api/v1/apartments/", timeout=10)
        if response.status_code == 200:
            apartments = response.json()
            apartment_codes = [apt['code'] for apt in apartments]
            
            if apartment_code not in apartment_codes:
                await update.message.reply_text(
                    f"❌ Apartamento '{apartment_code}' no encontrado.\n\n"
                    f"Apartamentos disponibles: {', '.join(apartment_codes)}"
                )
                return
            
            # Encontrar el apartamento y guardar ID
            apartment = next(apt for apt in apartments if apt['code'] == apartment_code)
            save_user_session(user_id, {
                "apartment_code": apartment_code,
                "apartment_id": apartment['id']
            })
            
            await update.message.reply_text(
                f"✅ Apartamento configurado: **{apartment_code}**\n"
                f"🏠 {apartment.get('name', 'Sin nombre')}\n\n"
                f"Ahora puedes enviar fotos de facturas 📸"
            )
        else:
            await update.message.reply_text("❌ Error obteniendo apartamentos del servidor.")
    except Exception as e:
        logger.error(f"Error en /usar: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def actual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /actual"""
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    
    apartment_code = session.get("apartment_code")
    if apartment_code:
        await update.message.reply_text(f"🏠 Apartamento actual: **{apartment_code}**")
    else:
        await update.message.reply_text(
            "❌ No tienes apartamento configurado.\n\n"
            "Usa: /usar SES01"
        )

async def reset_apartamento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /reset"""
    user_id = update.effective_user.id
    user_sessions.pop(user_id, None)
    await update.message.reply_text(
        "🔄 Apartamento olvidado.\n\n"
        "Usa /usar <codigo> para configurar uno nuevo."
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /status"""
    try:
        import requests
        
        # Verificar estado del sistema
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        db_response = requests.get(f"{API_BASE_URL}/db-status", timeout=10)
        
        if health_response.status_code == 200 and db_response.status_code == 200:
            # Obtener apartamentos
            apt_response = requests.get(f"{API_BASE_URL}/api/v1/apartments/", timeout=10)
            if apt_response.status_code == 200:
                apartments = apt_response.json()
                apt_list = "\n".join([f"• {apt['code']}: {apt.get('name', 'Sin nombre')}" for apt in apartments])
                
                await update.message.reply_text(
                    f"📊 **Estado del Sistema:**\n\n"
                    f"✅ API: Funcionando\n"
                    f"✅ Base de datos: Conectada\n"
                    f"✅ Bot: Operativo\n\n"
                    f"🏠 **Apartamentos disponibles ({len(apartments)}):**\n"
                    f"{apt_list}\n\n"
                    f"🌐 Dashboard: {API_BASE_URL}/api/v1/dashboard/"
                )
            else:
                await update.message.reply_text("✅ Sistema funcionando, pero error obteniendo apartamentos.")
        else:
            await update.message.reply_text("❌ Sistema no disponible temporalmente.")
    except Exception as e:
        logger.error(f"Error en /status: {e}")
        await update.message.reply_text(f"❌ Error verificando estado: {str(e)}")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejar fotos de facturas - VERSIÓN SIMPLIFICADA"""
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    
    apartment_code = session.get("apartment_code")
    apartment_id = session.get("apartment_id")
    
    if not apartment_code or not apartment_id:
        await update.message.reply_text(
            "❌ Primero configura tu apartamento:\n\n"
            "/usar SES01"
        )
        return
    
    await update.message.reply_text(
        f"📸 **Foto recibida para {apartment_code}**\n\n"
        f"⚠️ **Modo simplificado activo**\n"
        f"Por favor, introduce manualmente los datos del gasto:\n\n"
        f"**Formato:**\n"
        f"Fecha: YYYY-MM-DD\n"
        f"Importe: XX.XX\n"
        f"Proveedor: Nombre del proveedor\n"
        f"Categoría: Restauración/Transporte/etc.\n"
        f"Descripción: Descripción del gasto\n\n"
        f"**Ejemplo:**\n"
        f"2025-01-21\n"
        f"45.50\n"
        f"Restaurante El Buen Comer\n"
        f"Restauración\n"
        f"Cena de negocios"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejar texto para crear gastos manuales"""
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    
    apartment_code = session.get("apartment_code")
    apartment_id = session.get("apartment_id")
    
    if not apartment_code or not apartment_id:
        await update.message.reply_text("❌ Configura primero tu apartamento: /usar SES01")
        return
    
    text = update.message.text.strip()
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if len(lines) >= 4:  # Mínimo: fecha, importe, proveedor, categoría
        try:
            # Parsear datos básicos
            expense_data = {
                "apartment_id": apartment_id,
                "date": lines[0],
                "amount_gross": float(lines[1]),
                "vendor": lines[2],
                "category": lines[3],
                "description": lines[4] if len(lines) > 4 else lines[2],
                "currency": "EUR",
                "source": "telegram_bot_manual"
            }
            
            # Enviar al backend
            import requests
            headers = {
                "Content-Type": "application/json",
                "X-Internal-Key": INTERNAL_KEY
            }
            
            response = requests.post(
                f"{API_BASE_URL}/api/v1/expenses/",
                json=expense_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                await update.message.reply_text(
                    f"✅ **Gasto registrado correctamente!**\n\n"
                    f"📅 Fecha: {expense_data['date']}\n"
                    f"💰 Importe: €{expense_data['amount_gross']}\n"
                    f"🏪 Proveedor: {expense_data['vendor']}\n"
                    f"📂 Categoría: {expense_data['category']}\n"
                    f"🏠 Apartamento: {apartment_code}\n\n"
                    f"🆔 ID: {result.get('expense_id', 'N/A')}\n\n"
                    f"🌐 Ver en dashboard: {API_BASE_URL}/api/v1/dashboard/"
                )
            else:
                await update.message.reply_text(f"❌ Error creando gasto: {response.status_code} - {response.text}")
                
        except ValueError as e:
            await update.message.reply_text(
                f"❌ Error en el formato de datos.\n\n"
                f"Asegúrate de usar el formato:\n"
                f"Fecha (YYYY-MM-DD)\n"
                f"Importe (número)\n"
                f"Proveedor\n"
                f"Categoría\n"
                f"Descripción (opcional)"
            )
        except Exception as e:
            logger.error(f"Error creando gasto manual: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    else:
        await update.message.reply_text(
            f"📝 **Formato incorrecto**\n\n"
            f"Envía los datos en líneas separadas:\n"
            f"1. Fecha (YYYY-MM-DD)\n"
            f"2. Importe (ejemplo: 45.50)\n"
            f"3. Proveedor\n"
            f"4. Categoría\n"
            f"5. Descripción (opcional)\n\n"
            f"**Ejemplo:**\n"
            f"2025-01-21\n"
            f"45.50\n"
            f"Restaurante El Buen Comer\n"
            f"Restauración\n"
            f"Cena de negocios"
        )

async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejar mensajes no reconocidos"""
    await update.message.reply_text(
        "🤔 **No entiendo ese mensaje.**\n\n"
        "📋 **Comandos disponibles:**\n"
        "• /start - Iniciar bot\n"
        "• /usar <codigo> - Configurar apartamento\n"
        "• /actual - Ver apartamento actual\n"
        "• /reset - Resetear apartamento\n"
        "• /status - Estado del sistema\n\n"
        "📸 **O envía una foto de factura** (modo manual)\n"
        "📝 **O envía datos en formato texto** (ver /start para formato)"
    )

def main():
    """Función principal del bot de producción"""
    if not TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN no configurado")
        raise RuntimeError("TELEGRAM_TOKEN requerido")
    
    if not OPENAI_API_KEY:
        logger.warning("⚠️ OPENAI_API_KEY no configurado - modo manual solamente")
    
    if not INTERNAL_KEY:
        logger.warning("⚠️ INTERNAL_KEY no configurado - puede haber errores de autenticación")
    
    logger.info(f"🤖 Iniciando bot de producción...")
    logger.info(f"🌐 API_BASE_URL: {API_BASE_URL}")
    logger.info(f"🔑 TELEGRAM_TOKEN: {'✅ Configurado' if TELEGRAM_TOKEN else '❌ Faltante'}")
    logger.info(f"🧠 OPENAI_API_KEY: {'✅ Configurado' if OPENAI_API_KEY else '❌ Faltante'}")
    logger.info(f"🔐 INTERNAL_KEY: {'✅ Configurado' if INTERNAL_KEY else '❌ Faltante'}")
    
    # Crear aplicación
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Agregar handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("usar", usar_apartamento))
    app.add_handler(CommandHandler("actual", actual))
    app.add_handler(CommandHandler("reset", reset_apartamento))
    app.add_handler(CommandHandler("status", status_command))
    
    # Handler para fotos (modo manual)
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Handler para texto (crear gastos manuales)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Handler para mensajes no reconocidos
    app.add_handler(MessageHandler(filters.ALL & ~filters.PHOTO & ~filters.TEXT, handle_unknown))
    
    logger.info("🚀 Bot de producción iniciado y escuchando...")
    logger.info("📱 Comandos disponibles: /start, /usar, /actual, /reset, /status")
    logger.info("📸 Modo: Manual (sin OCR automático)")
    
    try:
        # Ejecutar bot
        app.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"❌ Error ejecutando bot: {e}")
        raise

if __name__ == "__main__":
    main()