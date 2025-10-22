#!/usr/bin/env python3
"""
Script para probar el arreglo del webhook de Telegram
"""
import asyncio
import os
import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

async def test_webhook_initialization():
    """Probar la inicialización del webhook"""
    print("🔧 Probando inicialización del webhook...")
    
    # Verificar variables de entorno
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    if not telegram_token:
        print("❌ TELEGRAM_TOKEN no configurado")
        return False
    
    print(f"✅ TELEGRAM_TOKEN configurado: ...{telegram_token[-4:]}")
    
    try:
        # Importar y probar inicialización
        from app.webhook_bot import ensure_telegram_app_initialized
        
        print("📱 Inicializando aplicación de Telegram...")
        app = await ensure_telegram_app_initialized()
        
        if not app:
            print("❌ No se pudo inicializar la aplicación")
            return False
        
        print("✅ Aplicación inicializada correctamente")
        
        # Probar obtener información del bot
        print("🤖 Obteniendo información del bot...")
        bot_info = await app.bot.get_me()
        print(f"✅ Bot: @{bot_info.username} ({bot_info.first_name})")
        
        # Probar obtener información del webhook
        print("🔗 Verificando estado del webhook...")
        webhook_info = await app.bot.get_webhook_info()
        print(f"📍 Webhook URL: {webhook_info.url or 'No configurado'}")
        print(f"📊 Updates pendientes: {webhook_info.pending_update_count}")
        
        if webhook_info.last_error_message:
            print(f"⚠️ Último error: {webhook_info.last_error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

async def test_webhook_setup():
    """Probar configuración del webhook"""
    print("\n🔧 Probando configuración del webhook...")
    
    try:
        from app.webhook_bot import ensure_telegram_app_initialized
        
        app = await ensure_telegram_app_initialized()
        if not app:
            print("❌ No se pudo inicializar la aplicación")
            return False
        
        # URL del webhook (usar localhost para pruebas locales)
        webhook_url = "https://ses-gastos.onrender.com/webhook/telegram"
        print(f"🔗 Configurando webhook: {webhook_url}")
        
        # Configurar webhook
        success = await app.bot.set_webhook(url=webhook_url)
        
        if success:
            print("✅ Webhook configurado correctamente")
            
            # Verificar configuración
            webhook_info = await app.bot.get_webhook_info()
            print(f"📍 URL configurada: {webhook_info.url}")
            print(f"📊 Updates pendientes: {webhook_info.pending_update_count}")
            
            return True
        else:
            print("❌ No se pudo configurar el webhook")
            return False
            
    except Exception as e:
        print(f"❌ Error configurando webhook: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Función principal"""
    print("🚀 Iniciando pruebas del webhook de Telegram...\n")
    
    # Prueba 1: Inicialización
    init_success = await test_webhook_initialization()
    
    if init_success:
        # Prueba 2: Configuración del webhook
        setup_success = await test_webhook_setup()
        
        if setup_success:
            print("\n✅ ¡Todas las pruebas pasaron!")
            print("\n📋 Próximos pasos:")
            print("1. Despliega los cambios en Render")
            print("2. Ve a /bot/webhook-status para verificar el estado")
            print("3. Prueba el bot enviando /start en Telegram")
            print("4. Si funciona, envía /usar SES01 y luego una foto")
        else:
            print("\n⚠️ La inicialización funciona pero hay problemas con el webhook")
    else:
        print("\n❌ Hay problemas con la inicialización básica")
        print("\n🔧 Verifica:")
        print("- TELEGRAM_TOKEN está configurado correctamente")
        print("- La conexión a internet funciona")
        print("- No hay problemas con las dependencias")

if __name__ == "__main__":
    asyncio.run(main())