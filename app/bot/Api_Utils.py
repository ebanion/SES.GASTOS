# utils/api.py
from __future__ import annotations

import time
import requests
from datetime import datetime
from decimal import Decimal, InvalidOperation

from dotenv import load_dotenv
load_dotenv()

# --- Helpers de normalización -------------------------

_ALLOWED_KEYS = {
    "apartment_id", "date", "amount_gross", "currency", "category",
    "description", "vendor", "invoice_number", "source", "vat_rate",
    "file_url", "status"
}

_ALIAS_MAP = {
    # mapeos comunes que pueden venir del LLM/OCR
    "amount": "amount_gross",
    "importe": "amount_gross",
    "total": "amount_gross",
    "fecha": "date",
    "moneda": "currency",
    "categoria": "category",
    "proveedor": "vendor",
    "num_factura": "invoice_number",
    "n_factura": "invoice_number",
}

def _parse_date_yyyy_mm_dd(value: str) -> str:
    """
    Devuelve la fecha en formato YYYY-MM-DD.
    Acepta formatos típicos: DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY, etc.
    """
    if not value:
        return value
    s = str(value).strip()
    # ya formateada?
    try:
        dt = datetime.strptime(s, "%Y-%m-%d")  # YYYY-MM-DD
        return dt.date().isoformat()
    except ValueError:
        pass

    # DD/MM/YYYY y variantes
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.date().isoformat()
        except ValueError:
            continue

    # último intento: si viene con hora, extrae fecha
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.date().isoformat()
    except Exception:
        return s  # deja pasar

def _to_decimal_string(val) -> str | None:
    """
    Convierte a string decimal seguro para que Pydantic lo parsee como Decimal.
    Acepta str, int, float, Decimal. Deja None si no puede.
    """
    if val is None:
        return None
    try:
        d = Decimal(str(val))
        return str(d)
    except (InvalidOperation, ValueError, TypeError):
        return None

def _normalize_expense_dict(d: dict) -> dict:
    """
    1) Aplica alias de claves.
    2) Normaliza currency (upper), date (YYYY-MM-DD), amount_gross (Decimal string).
    3) Filtra únicamente claves admitidas por el backend.
    """
    data = dict(d or {})

    # 1) Alias
    for k, v in list(data.items()):
        lk = str(k).strip()
        if lk in _ALIAS_MAP:
            target = _ALIAS_MAP[lk]
            if target not in data or not data[target]:
                data[target] = v
            if lk != target:
                data.pop(k, None)

    # 2) Normalizaciones
    if "currency" in data and isinstance(data["currency"], str):
        data["currency"] = data["currency"].strip().upper()

    if "date" in data and data["date"]:
        data["date"] = _parse_date_yyyy_mm_dd(data["date"])

    if "amount_gross" in data:
        data["amount_gross"] = _to_decimal_string(data["amount_gross"])

    # 3) Filtra claves válidas
    cleaned = {k: v for k, v in data.items() if k in _ALLOWED_KEYS and v is not None}
    return cleaned

# --- Client API ---------------------------------------

def get_apartment_id_by_code(
    api_base_url: str,
    internal_key: str,
    code: str,
    timeout: int = 40,
    retries: int = 2,
) -> str | None:
    """
    Pide al backend el apartamento por su código y devuelve el 'id'.
    Reintenta ante timeouts/conexiones (Render frío o lento).
    """
    url = f"{api_base_url.rstrip('/')}/api/v1/apartments/by_code/{code}"
    headers = {"X-Internal-Key": internal_key, "Accept": "application/json"}

    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            if r.status_code == 200:
                data = r.json()
                return data.get("id")
            if r.status_code == 404:
                return None  # código no existe
            # otros errores HTTP explícitos
            raise RuntimeError(f"[by_code] {r.status_code} {r.text}")
        except (
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ConnectionError,
        ) as e:
            last_err = e
            if attempt < retries:
                time.sleep(1 * (attempt + 1))  # 1s, 2s...
            else:
                break

    # agotados reintentos
    raise RuntimeError(f"Timeout/Conexión validando código '{code}': {last_err}")

def send_expense_to_backend(expense_data: dict, api_base_url: str, internal_key: str) -> tuple[bool, str]:
    """
    Envía el gasto al backend. Si llega apartment_code (pero no apartment_id),
    resuelve el id primero. Devuelve (ok, mensaje_respuesta).
    """
    if not api_base_url:
        return (False, "API_BASE_URL no configurado")
    if not internal_key:
        return (False, "INTERNAL_KEY no configurado")

    api_base = api_base_url.rstrip("/")
    headers = {
        "X-Internal-Key": internal_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    payload = dict(expense_data or {})

    # 0) Resolver apartment_id si hace falta
    apt_id = payload.get("apartment_id")
    apt_code = payload.get("apartment_code")
    if not apt_id:
        if not apt_code:
            return (False, "Falta apartment_code o apartment_id")
        # timeout largo + reintentos para cold start
        resolved = get_apartment_id_by_code(api_base, internal_key, apt_code, timeout=40, retries=2)
        if not resolved:
            return (False, f"apartment_code '{apt_code}' no encontrado")
        payload["apartment_id"] = resolved

    # 1) Normaliza y limpia payload para el backend
    payload.pop("apartment_code", None)
    payload = _normalize_expense_dict(payload)

    # Validaciones mínimas antes de enviar
    missing = [k for k in ("apartment_id", "date", "amount_gross", "currency") if not payload.get(k)]
    if missing:
        return (False, f"Faltan campos obligatorios: {', '.join(missing)}")

    # 2) POST al backend
    url = f"{api_base}/api/v1/expenses"
    r = requests.post(url, json=payload, headers=headers, timeout=20)

    if r.status_code in (200, 201):
        return (True, r.text)

    if r.status_code == 403:
        return (False, "Forbidden: X-Internal-Key no coincide con ADMIN_KEY del backend")

    if r.status_code == 404:
        return (False, r.text)  # p.ej. apartment_not_found

    # devuelve cuerpo para diagnóstico rápido
    return (False, f"HTTP {r.status_code}: {r.text}")
