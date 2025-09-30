import httpx, uuid
from .config import settings

def _ses_url(path: str) -> str:
    if not settings.SES_BASE_URL:
        return ""
    return f"{settings.SES_BASE_URL}{path}"

def notify_ses_reservation_created(payload: dict, idempotency_key: str):
    """
    Fuego y olvido: publicamos en SES (crea reserva + genera links).
    Si falla, no rompemos el flujo de creación de reserva.
    """
    if not settings.SES_BASE_URL:
        return

    headers = {settings.IDEMPOTENCY_HEADER: idempotency_key}
    with httpx.Client(timeout=6.0) as client:
        # 1) Crear la reserva en el servicio POLICÍA
        r = client.post(_ses_url("/api/bookings"), json={
            "check_in": payload["check_in"],
            "check_out": payload["check_out"],
            "guests": payload["guests"],
            "channel": payload.get("channel", "manual"),
            "email": payload.get("email"),
            "phone": payload.get("phone"),
        }, headers=headers)
        r.raise_for_status()
        booking_id = r.json().get("booking_id")

        # 2) Generar enlaces
        client.post(_ses_url(f"/api/bookings/{booking_id}/links"), headers=headers)
