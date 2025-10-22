# app/bot_config.py
"""
Configuración del bot para producción
"""
import os

class BotConfig:
    """Configuración del bot de Telegram"""
    
    # Tokens y claves
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    INTERNAL_KEY = os.getenv("INTERNAL_KEY") or os.getenv("ADMIN_KEY")
    
    # URLs
    API_BASE_URL = os.getenv("API_BASE_URL", "https://ses-gastos.onrender.com")
    
    # Configuración de OCR
    TESSERACT_CMD = os.getenv("TESSERACT_CMD", "/usr/bin/tesseract")  # Para Linux/Render
    
    @classmethod
    def is_configured(cls) -> bool:
        """Verificar si el bot está configurado correctamente"""
        return bool(cls.TELEGRAM_TOKEN and cls.OPENAI_API_KEY)
    
    @classmethod
    def get_config_status(cls) -> dict:
        """Obtener estado de configuración"""
        return {
            "telegram_token": bool(cls.TELEGRAM_TOKEN),
            "openai_api_key": bool(cls.OPENAI_API_KEY),
            "internal_key": bool(cls.INTERNAL_KEY),
            "api_base_url": cls.API_BASE_URL,
            "tesseract_cmd": cls.TESSERACT_CMD
        }