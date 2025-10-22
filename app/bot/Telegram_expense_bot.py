# bot/main.py  (Telegram_expense_bot.py)
from __future__ import annotations

import os
import json
import logging
import tempfile
from uuid import uuid4
from pathlib import Path
import unicodedata  # <-- nuevo

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)

from dotenv import load_dotenv
load_dotenv()  # Carga .env

# Importaciones relativas para cuando se ejecuta como módulo
try:
    from .Ocr_untils import extract_text_from_pdf, extract_text_from_image
    from .Llm_Untils import extract_expense_json
    from .Api_Utils import send_expense_to_backend, get_apartment_id_by_code
except ImportError:
    # Importaciones absolutas para cuando se ejecuta directamente
    from Ocr_untils import extract_text_from_pdf, extract_text_from_image
    from Llm_Untils import extract_expense_json
    from Api_Utils import send_expense_to_backend, get_apartment_id_by_code

# ---------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------
# 1) Token: .env > token.txt
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN and Path("token.txt").exists():
    TELEGRAM_TOKEN = Path("token.txt").read_text(encoding="utf-8").strip()

INTERNAL_KEY = os.getenv("INTERNAL_KEY")  # Debe coincidir con ADMIN_KEY (backend)
API_BASE_URL = os.getenv("API_BASE_URL") or os.getenv("API_URL") or "http://localhost:8000"

# 2) Estado por usuario (persistente)
SESSIONS_FILE = Path("sessions.json")
def _load_sessions() -> dict[int, dict[str, str]]:
    try:
        if SESSIONS_FILE.exists():
            data = json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
            # claves de JSON vienen como str; convertimos a int
            return {int(k): v for k, v in data.items()}
    except Exception:
        pass
    return {}

def _save_sessions():
    try:
        tmp = {str(k): v for k, v in dialog_context.items()}
        SESSIONS_FILE.write_text(json.dumps(tmp, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"[BOT] No pude guardar sessions.json: {e}")

dialog_context: dict[int, dict[str, str]] = _load_sessions()  # user_id -> {"apartment_code": "...", "apartment_id": "..."}

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("expense_bot")


# ---------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "Usuario"
    await update.message.reply_text(
        f"¡Hola {user_name}! 👋\n\n"
        "🤖 Soy el bot de SES.GASTOS. Puedo procesar automáticamente tus facturas y registrar gastos.\n\n"
        "📋 **Pasos para empezar:**\n"
        "1️⃣ Configura tu apartamento: /usar SES01\n"
        "2️⃣ Envía una foto 📸 o PDF 📄 de tu factura\n"
        "3️⃣ ¡Listo! El gasto se registra automáticamente\n\n"
        "🔧 **Comandos útiles:**\n"
        "• /actual - Ver apartamento configurado\n"
        "• /reset - Cambiar de apartamento\n\n"
        "💡 **Tip:** Asegúrate de que las fotos sean claras y legibles para mejores resultados."
    )

async def usar_apartamento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) != 1:
        await update.message.reply_text("Uso: /usar <codigo_apartamento>\nEj: /usar SES01")
        return

    code = (context.args[0] or "").strip().upper()
    if not code:
        await update.message.reply_text("Código vacío. Ej: /usar SES01")
        return

    # Validación contra backend: obtenemos el id real y lo cacheamos
    try:
        apt_id = get_apartment_id_by_code(API_BASE_URL, INTERNAL_KEY, code, timeout=40, retries=2)
    except Exception as e:
        logger.exception("Error consultando backend para validar código:")
        await update.message.reply_text(
            "⚠️ El backend está lento o despertando. Prueba de nuevo en unos segundos.\n"
            f"Detalle técnico: {e}"
        )
        return

    if not apt_id:
        await update.message.reply_text(f"❌ Código '{code}' no encontrado en el backend.")
        return

    dialog_context[user_id] = {"apartment_code": code, "apartment_id": apt_id}
    _save_sessions()
    await update.message.reply_text(f"✅ Apartamento activo: {code}")

async def actual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ctx = dialog_context.get(user_id, {})
    code = ctx.get("apartment_code")
    apt_id = ctx.get("apartment_id")
    if code and apt_id:
        await update.message.reply_text(f"🏷️ Apartamento activo: {code}\n🆔 ID: {apt_id}")
    else:
        await update.message.reply_text("No hay apartamento activo. Usa /usar <codigo>.")

async def reset_apartamento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in dialog_context:
        dialog_context.pop(user_id, None)
        _save_sessions()
    await update.message.reply_text("🧹 He olvidado tu apartamento activo. Usa /usar <codigo> para fijar uno.")


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _ensure_dict(obj) -> dict:
    """Asegura que lo que devuelve el LLM sea un dict (si viene string JSON, lo parsea)."""
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, str):
        try:
            return json.loads(obj)
        except Exception:
            return {"raw": obj}
    return dict(obj or {})

def _norm(s: str) -> str:
    """minúsculas + sin acentos (sólo stdlib)"""
    s = (s or "").lower()
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))

def _infer_category(expense: dict) -> str:
    """
    Heurística con prioridad por PROVEEDOR conocido.
    Si no hay match fuerte, cae a palabras genéricas y, por último, 'otros'.
    """
    text = _norm(f"{expense.get('vendor', '')} {expense.get('description', '')}")

    # ---- PRIORIDAD: proveedores/marcas (fuerte) ----
    if any(k in text for k in (
        "gesternova", "iberdrola", "endesa", "naturgy", "holaluz",
        "factorenergia", "fenie", "repsol luz", "totalenergies"
    )):
        return "electricidad"

    if any(k in text for k in (
        "canal isabel", "emmasa", "hidralia", "acsa", "aqualia",
        "aguas de ", "emasesa"
    )):
        return "agua"

    if any(k in text for k in (
        "gas natural", "naturgy gas", "repsol gas", "nedgia", "gnf",
        "propano", "butano"
    )):
        return "gas"

    if any(k in text for k in (
        "movistar", "orange", "vodafone", "masmovil", "o2", "jazztel",
        "lowi", "yoigo", "digi", "pepephone", "finetwork"
    )):
        return "telecomunicaciones"

    # ---- PALABRAS GENÉRICAS (medio) ----
    if any(k in text for k in ("luz", "energia", "electricidad", "kwh")):
        return "electricidad"
    if "agua" in text:
        return "agua"
    if any(k in text for k in ("fibra", "internet", "telefono", "telefonia", "adsl", "router")):
        return "telecomunicaciones"

    # ---- MANTENIMIENTO/servicios (débil) ----
    if any(k in text for k in (
        "limpieza", "mantenimiento", "reparacion", "fontaneria",
        "electricista", "cerrajeria", "pintura", "jardineria"
    )):
        return "mantenimiento"

    # ---- comodín suministros ----
    if any(k in text for k in ("suministro", "consumo", "utility", "factura")):
        return "suministros"

    return "otros"


# ---------------------------------------------------------------------
# PDF handler
# ---------------------------------------------------------------------
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages (facturas en imagen)"""
    user_id = update.effective_user.id
    
    try:
        # 1) Necesitamos apartamento activo
        ctx = dialog_context.get(user_id, {})
        base_code = ctx.get("apartment_code")
        base_id = ctx.get("apartment_id")
        if not base_code or not base_id:
            await update.message.reply_text("❌ Primero indica el código del apartamento con /usar <codigo>\n\nEjemplo: /usar SES01")
            return

        await update.message.reply_text("📸 Procesando imagen de factura...")
        
        # 2) Obtener la foto de mayor resolución
        photo = update.message.photo[-1]  # La última es la de mayor resolución
        file = await photo.get_file()
        
        # 3) Descargar a archivo temporal
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            await file.download_to_drive(tmp_path)
        
        # 4) Extraer texto usando OCR
        from Ocr_untils import extract_text_from_image
        texto_extraido = extract_text_from_image(tmp_path)
        
        if not texto_extraido or len(texto_extraido.strip()) < 10:
            await update.message.reply_text("❌ No pude extraer texto de la imagen. Asegúrate de que la foto sea clara y legible.")
            return
        
        # 5) Procesar con IA
        await _process_expense_text(update, user_id, base_code, base_id, texto_extraido, "foto")
        
    except Exception as e:
        logger.error(f"Error procesando foto: {e}")
        await update.message.reply_text(f"❌ Error procesando la imagen: {str(e)}")
    finally:
        # Limpiar archivo temporal
        try:
            if 'tmp_path' in locals():
                os.unlink(tmp_path)
        except:
            pass

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        # 1) Necesitamos apartamento activo
        ctx = dialog_context.get(user_id, {})
        base_code = ctx.get("apartment_code")
        base_id = ctx.get("apartment_id")
        if not base_code or not base_id:
            await update.message.reply_text("❌ Primero indica el código del apartamento con /usar <codigo>\n\nEjemplo: /usar SES01")
            return

        # 2) Verificar que es PDF
        doc = update.message.document
        if not doc or (not (doc.file_name or "").lower().endswith(".pdf") and (doc.mime_type or "") != "application/pdf"):
            await update.message.reply_text("❌ Solo acepto archivos PDF.")
            return
        
        await update.message.reply_text("📄 Procesando PDF de factura...")

    # 3) Descargar a archivo temporal
    file = await doc.get_file()
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp_path = tmp.name
        await file.download_to_drive(tmp_path)
        logger.info(f"[BOT] PDF guardado en {tmp_path}")

        # 4) OCR
        try:
            text = extract_text_from_pdf(tmp_path) or ""
        except Exception as e:
            logger.exception("Error en OCR:")
            await update.message.reply_text(f"❌ Error extrayendo texto (OCR): {e}")
            return

        text_preview = text[:200].replace("\n", " ")
        logger.info(f"[BOT] Texto extraído (preview): {text_preview}...")

        if not text.strip():
            await update.message.reply_text(
                "⚠️ No pude extraer texto del PDF. ¿Es una imagen borrosa?\n"
                "Intenta con un PDF más legible."
            )
            return

        # 5) LLM → JSON
        try:
            expense_json = extract_expense_json(text, base_code)
        except Exception as e:
            logger.exception("Error en LLM:")
            await update.message.reply_text(f"❌ Error interpretando el ticket con IA: {e}")
            return

        expense = _ensure_dict(expense_json)

        # Forzamos destino correcto del gasto
        expense["apartment_code"] = base_code
        expense["apartment_id"] = base_id  # <-- evita lookup adicional en API_Utils

        # === BLOQUE IVA (defensa) ===
        # Si no viene vat_rate (o viene 0/None), aplicamos 21% por defecto
        if not expense.get("vat_rate"):
            expense["vat_rate"] = 21.0
            logger.info(f"[BOT] vat_rate por defecto aplicado: {expense['vat_rate']}")

        # Si tenemos amount_gross y no viene amount_vat/net, los calculamos
        if expense.get("amount_gross") and not expense.get("amount_vat"):
            try:
                expense["amount_vat"] = round(float(expense["amount_gross"]) * float(expense["vat_rate"]) / 100, 2)
                expense["amount_net"] = round(float(expense["amount_gross"]) - float(expense["amount_vat"]), 2)
                logger.info(f"[BOT] amount_vat/net calculados: {expense['amount_vat']} / {expense['amount_net']}")
            except Exception:
                # Si por cualquier razón no podemos calcular, seguimos; el backend al menos tendrá vat_rate
                pass
        # === FIN BLOQUE IVA ===

        # Asegurar categoría (evitar NOT NULL en backend)
        if not expense.get("category"):
            expense["category"] = _infer_category(expense)
            logger.info(f"[BOT] category inferida: {expense['category']}")

        logger.info(f"[BOT] JSON generado: {expense}")

        # 6) Validaciones mínimas ANTES de enviar al backend
        required_fields = ["apartment_id", "date", "amount_gross", "currency", "category"]
        missing = [f for f in required_fields if not expense.get(f)]
        if missing:
            await update.message.reply_text(
                "⚠️ Faltan datos obligatorios: "
                + ", ".join(missing)
                + ".\nRevisa el ticket o indícalos manualmente."
            )
            return

        # 7) POST al backend (con manejo de errores de red)
        try:
            ok, msg = send_expense_to_backend(expense, API_BASE_URL, INTERNAL_KEY)
        except Exception as e:
            logger.exception("Error al llamar al backend:")
            await update.message.reply_text(
                "❌ No pude contactar con el backend ahora mismo.\n"
                "Puede estar lento o en frío. Intenta otra vez en unos segundos.\n"
                f"Detalle técnico: {e}"
            )
            return

        if ok:
            await update.message.reply_text(f"✅ Gasto registrado correctamente en el sistema (🏷️ {base_code}).")
        else:
            await update.message.reply_text(f"❌ Error al registrar gasto:\n{msg}")

    finally:
        # 8) Limpieza del temporal
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


# ---------------------------------------------------------------------
async def handle_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown text messages"""
    await update.message.reply_text(
        "🤔 No entiendo ese mensaje.\n\n"
        "📋 Comandos disponibles:\n"
        "• /start - Iniciar\n"
        "• /usar <codigo> - Configurar apartamento (ej: /usar SES01)\n"
        "• /actual - Ver apartamento actual\n"
        "• /reset - Resetear apartamento\n\n"
        "📸 O envía una foto/PDF de una factura para procesarla automáticamente."
    )

async def _process_expense_text(update, user_id, base_code, base_id, texto_extraido, source_type):
    """Función común para procesar texto extraído de facturas"""
    try:
        logger.info(f"Texto extraído (primeros 200 chars): {texto_extraido[:200]}")

        # 1) Llamar al LLM
        expense_json = extract_expense_json(texto_extraido)
        if not expense_json:
            await update.message.reply_text("❌ No pude extraer datos de gasto del texto.")
            return

        logger.info(f"JSON extraído: {expense_json}")

        # 2) Normalizar
        expense_json["apartment_id"] = base_id
        expense_json["source"] = f"telegram_bot_{source_type.lower()}"

        # 3) Enviar al backend
        response = send_expense_to_backend(expense_json, API_BASE_URL, INTERNAL_KEY)
        if response.get("success"):
            expense_id = response.get("expense_id", "?")
            
            # Mensaje de éxito con detalles
            details = []
            if expense_json.get("date"):
                details.append(f"📅 Fecha: {expense_json['date']}")
            if expense_json.get("amount_gross"):
                details.append(f"💰 Importe: €{expense_json['amount_gross']}")
            if expense_json.get("vendor"):
                details.append(f"🏪 Proveedor: {expense_json['vendor']}")
            if expense_json.get("category"):
                details.append(f"📂 Categoría: {expense_json['category']}")
            details.append(f"🏠 Apartamento: {base_code}")
            
            success_msg = f"✅ Factura procesada correctamente!\n\n" + "\n".join(details) + f"\n\n🆔 ID: {expense_id}"
            await update.message.reply_text(success_msg)
        else:
            error_msg = response.get("error", "Error desconocido")
            await update.message.reply_text(f"❌ Error guardando gasto: {error_msg}")

    except Exception as e:
        logger.error(f"Error procesando texto de {source_type}: {e}")
        await update.message.reply_text(f"❌ Error procesando {source_type}: {str(e)}")

# Main
# ---------------------------------------------------------------------
def main():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("Falta TELEGRAM_TOKEN en .env o token.txt")

    if not INTERNAL_KEY:
        logger.warning("INTERNAL_KEY vacío: el backend devolverá 403. Configúralo en .env")

    logger.info(f"API_BASE_URL: {API_BASE_URL}")
    logger.info(f"TELEGRAM_TOKEN configurado: {'Sí' if TELEGRAM_TOKEN else 'No'}")
    logger.info(f"OPENAI_API_KEY configurado: {'Sí' if os.getenv('OPENAI_API_KEY') else 'No'}")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Agregar handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("usar", usar_apartamento))
    app.add_handler(CommandHandler("actual", actual))
    app.add_handler(CommandHandler("reset", reset_apartamento))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Handler para mensajes no reconocidos
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_message))

    logger.info("🤖 Bot iniciado y escuchando...")
    logger.info("📋 Comandos disponibles:")
    logger.info("   /start - Iniciar bot")
    logger.info("   /usar <codigo> - Configurar apartamento")
    logger.info("   /actual - Ver apartamento actual")
    logger.info("   /reset - Resetear apartamento")
    logger.info("📸 Envía fotos o PDFs de facturas para procesarlas")
    
    try:
        app.run_polling()
    except Exception as e:
        logger.error(f"Error ejecutando bot: {e}")
        raise


if __name__ == "__main__":
    main()


