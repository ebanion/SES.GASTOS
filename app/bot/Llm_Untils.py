# Llm_Untils.py — versión solo SDK v1
from __future__ import annotations
import os, json, re
from typing import List, Dict
from dotenv import load_dotenv

# Carga .env desde la carpeta del script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY no configurada en .env")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# SDK v1
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

def _safe_json_loads(s: str) -> dict:
    s = (s or "").strip()
    if not s:
        return {}
    try:
        return json.loads(s)
    except Exception:
        m = re.search(r"\{.*\}", s, flags=re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    return {}

def extract_expense_json(raw_text: str, apartment_code: str) -> dict:
    system = (
        "Eres un extractor estricto. Devuelve EXCLUSIVAMENTE un JSON válido, sin texto adicional. "
        "Normaliza: 'date' en YYYY-MM-DD, 'currency' en mayúsculas (EUR por defecto si no está claro), "
        "'amount_gross' como número con punto decimal. Si falta un dato, omítelo."
    )

    user = f"""
Texto OCR de una factura/gasto:

<<<
{raw_text}
>>>

El gasto pertenece al apartamento con código: {apartment_code}.

Devuelve un JSON con esta forma (solo claves con datos):
{{
  "apartment_code": "{apartment_code}",
  "date": "YYYY-MM-DD",
  "amount_gross": 123.45,
  "currency": "EUR",
  "category": "mantenimiento",
  "description": "texto breve",
  "vendor": "proveedor",
  "invoice_number": "ABC123",
  "source": "telegram_bot",
  "vat_rate": 21,
  "file_url": null,
  "status": "PENDING"
}}
"""

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        temperature=0,
    )
    content = resp.choices[0].message.content or ""
    data = _safe_json_loads(content)

    # Defaults/asegurados
    if apartment_code and not data.get("apartment_code"):
        data["apartment_code"] = apartment_code
    data.setdefault("currency", "EUR")
    data.setdefault("source", "telegram_bot")
    data.setdefault("status", "PENDING")
    
    # Agregar fecha actual si no se proporcionó
    if not data.get("date"):
        from datetime import date
        data["date"] = date.today().isoformat()
    
    return data
