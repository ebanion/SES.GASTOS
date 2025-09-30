import os, httpx

SES_URL = os.getenv("SES_BASE_URL", "").rstrip("/")

def notify_ses_reservation_created(payload: dict):
    # Si no hay URL configurada, no hacemos nada
    if not SES_URL:
        return
    try:
        with httpx.Client(timeout=6.0) as client:
            r = client.post(f"{SES_URL}/api/bookings", json={
                "check_in": payload["check_in"],
                "check_out": payload["check_out"],
                "guests": payload["guests"],
                "channel": payload.get("channel", "manual"),
                "email": payload.get("email"),
                "phone": payload.get("phone"),
            })
            r.raise_for_status()
            booking_id = r.json().get("booking_id")
            client.post(f"{SES_URL}/api/bookings/{booking_id}/links")
    except Exception as e:
        print(f"[SES] notify failed: {e}")
