# app/telegram_bot_service.py
"""
Servicio de Telegram Bot integrado en FastAPI
"""
import os
import asyncio
import logging
import threading
from typing import Optional

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBotService:
    """Servicio para ejecutar el bot de Telegram en background"""
    
    def __init__(self):
        self.bot_task: Optional[asyncio.Task] = None
        self.bot_thread: Optional[threading.Thread] = None
        self.is_running = False
        
    def should_start_bot(self) -> bool:
        """Verificar si el bot debería iniciarse"""
        telegram_token = os.getenv("TELEGRAM_TOKEN")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not telegram_token:
            logger.warning("TELEGRAM_TOKEN no configurado - Bot deshabilitado")
            return False
            
        if not openai_key:
            logger.warning("OPENAI_API_KEY no configurado - Bot deshabilitado")
            return False
            
        logger.info("✅ Variables de entorno del bot configuradas correctamente")
        return True
    
    def start_bot_in_thread(self):
        """Iniciar el bot en un hilo separado"""
        if not self.should_start_bot():
            return
            
        if self.is_running:
            logger.info("Bot ya está ejecutándose")
            return
        
        def run_bot():
            """Función para ejecutar el bot en hilo separado"""
            try:
                logger.info("🤖 Iniciando bot de Telegram...")
                
                # Importar y ejecutar el bot
                from .bot.Telegram_expense_bot import main as bot_main
                bot_main()
                
            except Exception as e:
                logger.error(f"Error ejecutando bot: {e}")
        
        self.bot_thread = threading.Thread(target=run_bot, daemon=True)
        self.bot_thread.start()
        self.is_running = True
        logger.info("🚀 Bot de Telegram iniciado en hilo separado")
    
    def stop_bot(self):
        """Detener el bot"""
        if self.bot_task and not self.bot_task.done():
            self.bot_task.cancel()
            logger.info("🛑 Bot de Telegram detenido")
        
        self.is_running = False
    
    def get_status(self) -> dict:
        """Obtener estado del bot"""
        return {
            "bot_running": self.is_running,
            "telegram_token_configured": bool(os.getenv("TELEGRAM_TOKEN")),
            "openai_key_configured": bool(os.getenv("OPENAI_API_KEY")),
            "thread_alive": self.bot_thread.is_alive() if self.bot_thread else False
        }

# Instancia global del servicio
telegram_service = TelegramBotService()