# app/bot/Telegram_multiuser_bot.py
"""
Bot de Telegram con sistema multiusuario
"""
from __future__ import annotations

import os
import json
import logging
import tempfile
from uuid import uuid4
from pathlib import Path
import unicodedata

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
)

from dotenv import load_dotenv
load_dotenv()

# Importaciones del sistema multiusuario
try:
    from .Multiuser_Utils import (
        register_telegram_user, authenticate_user_by_email, get_user_by_telegram_id,
        get_user_accounts, switch_account, get_current_account, get_account_apartments,
        send_expense_to_account, format_user_status, format_apartments_list,
        save_user_cache_to_file, MultiuserBotError
    )
    from .Ocr_untils import extract_text_from_pdf, extract_text_from_image
    from .Llm_Untils import extract_expense_json
except ImportError:
    # Importaciones absolutas para cuando se ejecuta directamente
    from Multiuser_Utils import (
        register_telegram_user, authenticate_user_by_email, get_user_by_telegram_id,
        get_user_accounts, switch_account, get_current_account, get_account_apartments,
        send_expense_to_account, format_user_status, format_apartments_list,
        save_user_cache_to_file, MultiuserBotError
    )
    from Ocr_untils import extract_text_from_pdf, extract_text_from_image
    from Llm_Untils import extract_expense_json

# Configuración
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN and Path("token.txt").exists():
    TELEGRAM_TOKEN = Path("token.txt").read_text(encoding="utf-8").strip()

# Estado de usuarios (para flujos de registro/login)
USER_STATES = {}

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------- COMANDOS PRINCIPALES ----------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /start - Bienvenida y estado del usuario"""
    user_id = update.effective_user.id
    user_data = get_user_by_telegram_id(user_id)
    
    if user_data:
        # Usuario ya autenticado
        status = format_user_status(user_id)
        keyboard = [
            [InlineKeyboardButton("🏠 Ver Apartamentos", callback_data="apartments")],
            [InlineKeyboardButton("📊 Dashboard", callback_data="dashboard")],
            [InlineKeyboardButton("🔄 Cambiar Cuenta", callback_data="switch_account")],
            [InlineKeyboardButton("❓ Ayuda", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🏠 **SES.GASTOS - Sistema Multiusuario**\n\n{status}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        # Usuario nuevo
        keyboard = [
            [InlineKeyboardButton("🔑 Iniciar Sesión", callback_data="login")],
            [InlineKeyboardButton("📝 Registrarse", callback_data="register")],
            [InlineKeyboardButton("❓ Ayuda", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🏠 **Bienvenido a SES.GASTOS**\n\n"
            "Sistema de Gestión de Apartamentos con IA\n\n"
            "🎯 **¿Qué puedo hacer?**\n"
            "• Procesar facturas automáticamente con OCR + IA\n"
            "• Gestionar gastos e ingresos por apartamento\n"
            "• Dashboard web completo\n"
            "• Sistema multiusuario con cuentas independientes\n\n"
            "Para empezar, necesitas autenticarte:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /login - Iniciar proceso de login"""
    user_id = update.effective_user.id
    
    # Verificar si ya está autenticado
    if get_user_by_telegram_id(user_id):
        await update.message.reply_text(
            "✅ Ya estás autenticado.\n\nUsa /status para ver tu información."
        )
        return
    
    USER_STATES[user_id] = {"action": "login", "step": "email"}
    
    await update.message.reply_text(
        "🔑 **Iniciar Sesión**\n\n"
        "Por favor, envía tu **email** registrado:"
    )

async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /register - Iniciar proceso de registro"""
    user_id = update.effective_user.id
    
    # Verificar si ya está autenticado
    if get_user_by_telegram_id(user_id):
        await update.message.reply_text(
            "✅ Ya estás registrado y autenticado.\n\nUsa /status para ver tu información."
        )
        return
    
    USER_STATES[user_id] = {"action": "register", "step": "email"}
    
    await update.message.reply_text(
        "📝 **Registro de Nueva Cuenta**\n\n"
        "Vamos a crear tu cuenta de anfitrión paso a paso.\n\n"
        "**Paso 1/4:** Envía tu **email**:"
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /status - Mostrar estado del usuario"""
    user_id = update.effective_user.id
    status = format_user_status(user_id)
    
    keyboard = [
        [InlineKeyboardButton("🏠 Ver Apartamentos", callback_data="apartments")],
        [InlineKeyboardButton("🔄 Cambiar Cuenta", callback_data="switch_account")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        status,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def apartments_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /apartamentos - Listar apartamentos de la cuenta"""
    user_id = update.effective_user.id
    
    if not get_user_by_telegram_id(user_id):
        await update.message.reply_text(
            "❌ No estás autenticado.\n\nUsa /login para iniciar sesión."
        )
        return
    
    apartments_text = format_apartments_list(user_id)
    await update.message.reply_text(apartments_text, parse_mode='Markdown')

async def usar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /usar CODIGO - Configurar apartamento para gastos"""
    user_id = update.effective_user.id
    
    if not get_user_by_telegram_id(user_id):
        await update.message.reply_text(
            "❌ No estás autenticado.\n\nUsa /login para iniciar sesión."
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ **Uso correcto:**\n"
            "`/usar CODIGO_APARTAMENTO`\n\n"
            "Ejemplo: `/usar SES01`\n\n"
            "💡 Usa /apartamentos para ver tus códigos disponibles",
            parse_mode='Markdown'
        )
        return
    
    apartment_code = context.args[0].upper()
    
    # Verificar que el apartamento existe en la cuenta
    from .Multiuser_Utils import get_apartment_by_code
    apartment = get_apartment_by_code(user_id, apartment_code)
    
    if not apartment:
        await update.message.reply_text(
            f"❌ Apartamento **{apartment_code}** no encontrado en tu cuenta.\n\n"
            "💡 Usa /apartamentos para ver tus códigos disponibles",
            parse_mode='Markdown'
        )
        return
    
    # Guardar apartamento seleccionado en el contexto del usuario
    user_data = get_user_by_telegram_id(user_id)
    user_data["selected_apartment_code"] = apartment_code
    
    await update.message.reply_text(
        f"✅ **Apartamento configurado: {apartment_code}**\n"
        f"🏠 {apartment.get('name', 'Sin nombre')}\n\n"
        "Ahora puedes:\n"
        "📸 Enviar fotos de facturas para procesamiento automático\n"
        "💬 Escribir gastos manualmente\n"
        "📊 Ver dashboard: /dashboard\n\n"
        "💡 **Ejemplo de gasto manual:**\n"
        "`Restaurante La Playa, 45.50€, cena de negocios`",
        parse_mode='Markdown'
    )

async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /dashboard - Enlace al dashboard web"""
    user_id = update.effective_user.id
    
    if not get_user_by_telegram_id(user_id):
        await update.message.reply_text(
            "❌ No estás autenticado.\n\nUsa /login para iniciar sesión."
        )
        return
    
    current_account = get_current_account(user_id)
    if not current_account:
        await update.message.reply_text(
            "❌ No tienes una cuenta seleccionada.\n\nUsa /cuentas para seleccionar una."
        )
        return
    
    # URLs del dashboard
    api_base = os.getenv("API_BASE_URL", "https://ses-gastos.onrender.com")
    dashboard_url = f"{api_base}/multiuser/dashboard"
    
    keyboard = [
        [InlineKeyboardButton("📊 Abrir Dashboard", url=dashboard_url)],
        [InlineKeyboardButton("🏠 Ver Apartamentos", callback_data="apartments")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📊 **Dashboard de {current_account['name']}**\n\n"
        f"🏠 Apartamentos: {current_account.get('apartments_count', 0)}\n"
        f"📈 Plan: {current_account.get('subscription_status', 'trial').title()}\n\n"
        f"🔗 **Accede a tu dashboard web:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def cuentas_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /cuentas - Gestionar cuentas del usuario"""
    user_id = update.effective_user.id
    user_data = get_user_by_telegram_id(user_id)
    
    if not user_data:
        await update.message.reply_text(
            "❌ No estás autenticado.\n\nUsa /login para iniciar sesión."
        )
        return
    
    accounts = get_user_accounts(user_id)
    current_account_id = user_data.get("current_account_id")
    
    if len(accounts) <= 1:
        await update.message.reply_text(
            "ℹ️ Solo tienes una cuenta disponible.\n\n"
            "Para crear cuentas adicionales, visita el dashboard web."
        )
        return
    
    keyboard = []
    for account in accounts:
        is_current = account["id"] == current_account_id
        button_text = f"{'✅ ' if is_current else ''}🏢 {account['name']}"
        keyboard.append([InlineKeyboardButton(
            button_text, 
            callback_data=f"switch_account:{account['id']}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🏢 **Tus Cuentas Disponibles:**\n\n"
        "Selecciona la cuenta con la que quieres trabajar:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ---------- PROCESAMIENTO DE MENSAJES ----------

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejar mensajes de texto"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Verificar si está en un flujo de registro/login
    if user_id in USER_STATES:
        await handle_user_flow(update, context)
        return
    
    # Verificar autenticación
    user_data = get_user_by_telegram_id(user_id)
    if not user_data:
        await update.message.reply_text(
            "❌ No estás autenticado.\n\n"
            "Usa /start para comenzar o /login para iniciar sesión."
        )
        return
    
    # Verificar que tenga apartamento seleccionado
    selected_apartment = user_data.get("selected_apartment_code")
    if not selected_apartment:
        await update.message.reply_text(
            "❌ No tienes un apartamento configurado.\n\n"
            "Usa `/usar CODIGO` para configurar un apartamento.\n"
            "💡 Ejemplo: `/usar SES01`",
            parse_mode='Markdown'
        )
        return
    
    # Procesar como gasto manual
    await process_manual_expense(update, context, text, selected_apartment)

async def handle_user_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejar flujos de registro y login"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    state = USER_STATES.get(user_id, {})
    
    action = state.get("action")
    step = state.get("step")
    
    if action == "login":
        await handle_login_flow(update, context, text, state)
    elif action == "register":
        await handle_register_flow(update, context, text, state)

async def handle_login_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, state: dict) -> None:
    """Manejar flujo de login"""
    user_id = update.effective_user.id
    step = state.get("step")
    
    if step == "email":
        # Validar email básico
        if "@" not in text or "." not in text:
            await update.message.reply_text(
                "❌ Email inválido. Por favor, envía un email válido:"
            )
            return
        
        state["email"] = text
        state["step"] = "password"
        USER_STATES[user_id] = state
        
        await update.message.reply_text(
            f"📧 Email: **{text}**\n\n"
            "Ahora envía tu **contraseña**:",
            parse_mode='Markdown'
        )
    
    elif step == "password":
        email = state.get("email")
        password = text
        
        # Intentar autenticación
        success, message = authenticate_user_by_email(user_id, email, password)
        
        if success:
            del USER_STATES[user_id]  # Limpiar estado
            
            keyboard = [
                [InlineKeyboardButton("🏠 Ver Apartamentos", callback_data="apartments")],
                [InlineKeyboardButton("📊 Dashboard", callback_data="dashboard")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ **¡Autenticación exitosa!**\n\n{message}\n\n"
                "Ya puedes usar todas las funciones del bot:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ **Error de autenticación:**\n{message}\n\n"
                "Intenta de nuevo con /login"
            )
            del USER_STATES[user_id]

async def handle_register_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, state: dict) -> None:
    """Manejar flujo de registro"""
    user_id = update.effective_user.id
    step = state.get("step")
    
    if step == "email":
        if "@" not in text or "." not in text:
            await update.message.reply_text(
                "❌ Email inválido. Por favor, envía un email válido:"
            )
            return
        
        state["email"] = text
        state["step"] = "full_name"
        USER_STATES[user_id] = state
        
        await update.message.reply_text(
            f"📧 Email: **{text}**\n\n"
            "**Paso 2/4:** Envía tu **nombre completo**:",
            parse_mode='Markdown'
        )
    
    elif step == "full_name":
        if len(text) < 2:
            await update.message.reply_text(
                "❌ Nombre muy corto. Envía tu nombre completo:"
            )
            return
        
        state["full_name"] = text
        state["step"] = "account_name"
        USER_STATES[user_id] = state
        
        await update.message.reply_text(
            f"👤 Nombre: **{text}**\n\n"
            "**Paso 3/4:** Envía el **nombre de tu cuenta de anfitrión**\n"
            "(Ej: 'Apartamentos Costa Brava', 'Gestión Playa', etc.):",
            parse_mode='Markdown'
        )
    
    elif step == "account_name":
        if len(text) < 2:
            await update.message.reply_text(
                "❌ Nombre de cuenta muy corto. Envía un nombre descriptivo:"
            )
            return
        
        state["account_name"] = text
        state["step"] = "confirm"
        USER_STATES[user_id] = state
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirmar Registro", callback_data="confirm_register")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel_register")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📋 **Confirma tus datos:**\n\n"
            f"📧 Email: {state['email']}\n"
            f"👤 Nombre: {state['full_name']}\n"
            f"🏢 Cuenta: {text}\n\n"
            "¿Todo correcto?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def process_manual_expense(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, apartment_code: str) -> None:
    """Procesar gasto manual desde texto"""
    user_id = update.effective_user.id
    
    try:
        # Usar IA para extraer datos del texto
        expense_json = extract_expense_json(text, apartment_code)
        
        if not expense_json:
            await update.message.reply_text(
                "❌ No pude extraer información del gasto.\n\n"
                "💡 **Formato sugerido:**\n"
                "`Proveedor, importe€, descripción`\n\n"
                "**Ejemplo:**\n"
                "`Restaurante La Playa, 45.50€, cena de negocios`"
            )
            return
        
        # Agregar código de apartamento
        expense_json["apartment_code"] = apartment_code
        expense_json["source"] = "telegram_manual"
        
        # Enviar al backend
        success, message = send_expense_to_account(user_id, expense_json)
        
        if success:
            # Formatear respuesta exitosa
            amount = expense_json.get("amount_gross", 0)
            vendor = expense_json.get("vendor", "Sin proveedor")
            category = expense_json.get("category", "Sin categoría")
            
            await update.message.reply_text(
                f"✅ **Gasto registrado exitosamente**\n\n"
                f"🏠 Apartamento: **{apartment_code}**\n"
                f"💰 Importe: **{amount}€**\n"
                f"🏪 Proveedor: {vendor}\n"
                f"📂 Categoría: {category}\n\n"
                f"📊 Ve tu dashboard: /dashboard",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ **Error registrando gasto:**\n{message}"
            )
    
    except Exception as e:
        logger.error(f"Error procesando gasto manual: {e}")
        await update.message.reply_text(
            "❌ Error procesando el gasto. Inténtalo de nuevo."
        )

# ---------- PROCESAMIENTO DE IMÁGENES ----------

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejar fotos de facturas"""
    user_id = update.effective_user.id
    
    # Verificar autenticación
    user_data = get_user_by_telegram_id(user_id)
    if not user_data:
        await update.message.reply_text(
            "❌ No estás autenticado.\n\nUsa /login para iniciar sesión."
        )
        return
    
    # Verificar apartamento seleccionado
    selected_apartment = user_data.get("selected_apartment_code")
    if not selected_apartment:
        await update.message.reply_text(
            "❌ No tienes un apartamento configurado.\n\n"
            "Usa `/usar CODIGO` para configurar un apartamento.",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        "📸 **Procesando factura...**\n"
        "⏳ Extrayendo texto con OCR + IA..."
    )
    
    try:
        # Descargar imagen
        photo = update.message.photo[-1]  # Mejor calidad
        file = await context.bot.get_file(photo.file_id)
        
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            await file.download_to_drive(tmp_file.name)
            
            # Extraer texto con OCR
            ocr_text = extract_text_from_image(tmp_file.name)
            
            if not ocr_text:
                await update.message.reply_text(
                    "❌ No pude extraer texto de la imagen.\n\n"
                    "💡 **Consejos:**\n"
                    "• Asegúrate de que la imagen sea clara\n"
                    "• Evita sombras y reflejos\n"
                    "• Prueba con mejor iluminación"
                )
                return
            
            # Procesar con IA
            expense_json = extract_expense_json(ocr_text, selected_apartment)
            
            if not expense_json:
                await update.message.reply_text(
                    f"❌ No pude extraer datos de gasto de la imagen.\n\n"
                    f"📝 **Texto extraído:**\n{ocr_text[:500]}...\n\n"
                    f"💡 Puedes escribir el gasto manualmente"
                )
                return
            
            # Agregar metadatos
            expense_json["apartment_code"] = selected_apartment
            expense_json["source"] = "telegram_ocr"
            
            # Enviar al backend
            success, message = send_expense_to_account(user_id, expense_json)
            
            if success:
                # Respuesta exitosa con detalles
                amount = expense_json.get("amount_gross", 0)
                vendor = expense_json.get("vendor", "Sin proveedor")
                category = expense_json.get("category", "Sin categoría")
                date = expense_json.get("date", "Hoy")
                
                await update.message.reply_text(
                    f"✅ **¡Factura procesada exitosamente!**\n\n"
                    f"🏠 Apartamento: **{selected_apartment}**\n"
                    f"💰 Importe: **{amount}€**\n"
                    f"📅 Fecha: {date}\n"
                    f"🏪 Proveedor: {vendor}\n"
                    f"📂 Categoría: {category}\n\n"
                    f"🤖 **Procesado con IA automáticamente**\n"
                    f"📊 Ve tu dashboard: /dashboard",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"❌ **Error registrando gasto:**\n{message}\n\n"
                    f"📝 **Datos extraídos:**\n{json.dumps(expense_json, indent=2, ensure_ascii=False)}"
                )
    
    except Exception as e:
        logger.error(f"Error procesando imagen: {e}")
        await update.message.reply_text(
            "❌ Error procesando la imagen. Inténtalo de nuevo."
        )

# ---------- CALLBACKS ----------

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejar callbacks de botones inline"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "login":
        await login_command(query, context)
    elif data == "register":
        await register_command(query, context)
    elif data == "apartments":
        apartments_text = format_apartments_list(user_id)
        await query.edit_message_text(apartments_text, parse_mode='Markdown')
    elif data == "dashboard":
        await dashboard_command(query, context)
    elif data == "switch_account":
        await cuentas_command(query, context)
    elif data.startswith("switch_account:"):
        account_id = data.split(":", 1)[1]
        success, message = switch_account(user_id, account_id)
        
        if success:
            await query.edit_message_text(
                f"✅ {message}\n\n"
                "Usa /apartamentos para ver los apartamentos de esta cuenta.",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(f"❌ {message}")
    elif data == "confirm_register":
        await confirm_register(query, context)
    elif data == "cancel_register":
        user_id = query.from_user.id
        if user_id in USER_STATES:
            del USER_STATES[user_id]
        await query.edit_message_text("❌ Registro cancelado.")
    elif data == "help":
        await help_command(query, context)

async def confirm_register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Confirmar y ejecutar registro"""
    user_id = update.from_user.id
    state = USER_STATES.get(user_id, {})
    
    email = state.get("email")
    full_name = state.get("full_name")
    account_name = state.get("account_name")
    
    if not all([email, full_name, account_name]):
        await update.edit_message_text(
            "❌ Datos incompletos. Inicia el registro de nuevo con /register"
        )
        return
    
    # Ejecutar registro
    success, message = register_telegram_user(user_id, email, full_name, account_name)
    
    if success:
        del USER_STATES[user_id]  # Limpiar estado
        
        keyboard = [
            [InlineKeyboardButton("🏠 Ver Apartamentos", callback_data="apartments")],
            [InlineKeyboardButton("📊 Dashboard", callback_data="dashboard")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.edit_message_text(
            f"✅ **¡Registro exitoso!**\n\n{message}\n\n"
            "Tu cuenta de anfitrión está lista. Ahora puedes:\n"
            "• Crear apartamentos\n"
            "• Procesar facturas con IA\n"
            "• Gestionar gastos e ingresos\n\n"
            "🎉 ¡Bienvenido a SES.GASTOS!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.edit_message_text(
            f"❌ **Error en el registro:**\n{message}\n\n"
            "Inténtalo de nuevo con /register"
        )
        if user_id in USER_STATES:
            del USER_STATES[user_id]

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /help - Ayuda del bot"""
    help_text = """
🏠 **SES.GASTOS - Ayuda del Bot**

**🔑 Autenticación:**
/start - Comenzar e info del estado
/login - Iniciar sesión con cuenta existente
/register - Registrar nueva cuenta de anfitrión
/status - Ver estado actual

**🏠 Gestión de Apartamentos:**
/apartamentos - Ver apartamentos de tu cuenta
/usar CODIGO - Configurar apartamento activo
/cuentas - Cambiar entre tus cuentas

**💰 Gestión de Gastos:**
📸 Enviar foto de factura → Procesamiento automático con IA
💬 Escribir gasto → "Restaurante, 45€, cena negocios"

**📊 Dashboard:**
/dashboard - Acceder al dashboard web completo

**🤖 Funciones IA:**
• OCR automático de facturas
• Extracción inteligente de datos
• Categorización automática
• Detección de fechas, importes, proveedores

**💡 Ejemplos:**
`/usar SES01`
`Taxi aeropuerto, 25€, traslado`
`Supermercado Dia, 67.45€, compra semanal`

**🆘 Soporte:**
Si tienes problemas, contacta al administrador del sistema.
    """
    
    if hasattr(update, 'edit_message_text'):
        await update.edit_message_text(help_text, parse_mode='Markdown')
    else:
        await update.message.reply_text(help_text, parse_mode='Markdown')

# ---------- CONFIGURACIÓN DEL BOT ----------

def main():
    """Función principal del bot"""
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN no configurado")
        return
    
    print("🤖 Iniciando bot multiusuario...")
    
    # Crear aplicación
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Comandos
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("login", login_command))
    application.add_handler(CommandHandler("register", register_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("apartamentos", apartments_command))
    application.add_handler(CommandHandler("apartments", apartments_command))
    application.add_handler(CommandHandler("usar", usar_command))
    application.add_handler(CommandHandler("dashboard", dashboard_command))
    application.add_handler(CommandHandler("cuentas", cuentas_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ayuda", help_command))
    
    # Manejadores de mensajes
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.PDF, handle_photo))  # PDFs como fotos por ahora
    
    # Callbacks
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Guardar cache periódicamente
    def save_cache_job(context):
        save_user_cache_to_file()
    
    # Guardar cache cada 5 minutos
    application.job_queue.run_repeating(save_cache_job, interval=300, first=300)
    
    print("✅ Bot multiusuario iniciado correctamente")
    print(f"🔗 API Base URL: {os.getenv('API_BASE_URL', 'No configurada')}")
    
    # Ejecutar bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()