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

from Ocr_untils import extract_text_from_pdf
from Llm_Untils import extract_expense_json
from Api_Utils import send_expense_to_backend, get_apartment_id_by_code  # <-- usa apartment_id si lo pasamos

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
    await update.message.reply_text(
        "Hola! Envíame un PDF de un gasto y lo registraré automáticamente.\n"
        "Antes, dime el código del apartamento con /usar <codigo>\n\n"
        "Ejemplo: /usar SES01\n"
        "Consulta el activo con /actual\n"
        "Para olvidar el apartamento activo: /reset"
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
async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # 1) Necesitamos apartamento activo
    ctx = dialog_context.get(user_id, {})
    base_code = ctx.get("apartment_code")
    base_id = ctx.get("apartment_id")
    if not base_code or not base_id:
        await update.message.reply_text("Primero indica el código del apartamento con /usar <codigo>")
        return

    # 2) Verificar que es PDF
    doc = update.message.document
    if not doc or (not (doc.file_name or "").lower().endswith(".pdf") and (doc.mime_type or "") != "application/pdf"):
        await update.message.reply_text("Solo acepto archivos PDF.")
        return

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
# Main
# ---------------------------------------------------------------------
def main():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("Falta TELEGRAM_TOKEN en .env o token.txt")

    if not INTERNAL_KEY:
        logger.warning("INTERNAL_KEY vacío: el backend devolverá 403. Configúralo en .env")

    logger.info(f"API_BASE_URL: {API_BASE_URL}")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("usar", usar_apartamento))
    app.add_handler(CommandHandler("actual", actual))
    app.add_handler(CommandHandler("reset", reset_apartamento))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))

    logger.info("Bot iniciado y escuchando...")
    app.run_polling()


if __name__ == "__main__":
    main()


