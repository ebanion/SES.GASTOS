#!/usr/bin/env python3
"""
Bot de Telegram simplificado para probar que funciona sin OCR
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuración
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "https://ses-gastos.onrender.com")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user_name = update.effective_user.first_name or "Usuario"
    await update.message.reply_text(
        f"¡Hola {user_name}! 👋\n\n"
        f"🤖 Bot de SES.GASTOS funcionando correctamente!\n\n"
        f"📋 Comandos disponibles:\n"
        f"• /start - Este mensaje\n"
        f"• /test - Probar conexión\n"
        f"• /status - Estado del sistema\n\n"
        f"🌐 API: {API_BASE_URL}"
    )

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /test"""
    try:
        import requests
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            await update.message.reply_text("✅ Conexión con API exitosa!")
        else:
            await update.message.reply_text(f"❌ Error API: {response.status_code}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /status"""
    try:
        import requests
        
        # Verificar apartamentos
        response = requests.get(f"{API_BASE_URL}/api/v1/apartments/", timeout=10)
        if response.status_code == 200:
            apartments = response.json()
            apt_list = "\n".join([f"• {apt['code']}: {apt.get('name', 'Sin nombre')}" for apt in apartments[:5]])
            
            await update.message.reply_text(
                f"📊 Estado del Sistema:\n\n"
                f"🏠 Apartamentos disponibles: {len(apartments)}\n"
                f"{apt_list}\n\n"
                f"✅ Bot funcionando correctamente!"
            )
        else:
            await update.message.reply_text(f"❌ Error obteniendo apartamentos: {response.status_code}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    """Función principal del bot"""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN no configurado")
        return
    
    logger.info(f"🤖 Iniciando bot simple de prueba...")
    logger.info(f"API_BASE_URL: {API_BASE_URL}")
    
    # Crear aplicación
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Agregar handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CommandHandler("status", status_command))
    
    logger.info("🚀 Bot simple iniciado y escuchando...")
    
    # Ejecutar bot
    app.run_polling()

if __name__ == "__main__":
    main()