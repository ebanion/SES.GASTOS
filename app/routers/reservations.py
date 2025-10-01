import os
import hashlib, json, uuid
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from ..db import get_db
from .. import models, schemas
from ..services.events import notify_ses_reservation_created

router = APIRouter(prefix="/api/v1/reservations", tags=["reservations"])


def _hash_body(body: dict) -> str:
    return hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode("utf-8")).hexdigest()


# =========================
# 1) Alta normal (si GASTOS es quien inicia)
#    - Genera booking_id local
#    - Guarda en BD
#    - Notifica a POLICÍA en background (como tenías)
# =========================
@router.post("", response_model=schemas.ReservationOut)
def create_reservation(
    payload: schemas.ReservationIn,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
):
    data_dict = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()

    # Idempotencia simple
    body_hash = _hash_body(data_dict)
    if x_idempotency_key:
        idem = (
            db.query(models.IdempotencyKey)
            .filter(models.IdempotencyKey.key == x_idempotency_key)
            .first()
        )
        if idem:
            if idem.request_hash != body_hash:
                raise HTTPException(status_code=409, detail="Idempotency-Key en uso con otro cuerpo")
            return idem.response_json

    # Generamos booking_id propio (este flujo NO usa el de POLICÍA)
    booking_uuid = uuid.uuid4()

    r = models.Reservation(
        id=booking_uuid,
        check_in=payload.check_in,
        check_out=payload.check_out,
        guests=payload.guests,
        channel=payload.channel,
        email_contact=payload.email,
        phone_contact=payload.phone,
    )

    try:
        db.add(r)
        db.commit()
        db.refresh(r)
    except Exception as e:
        db.rollback()
        print(f"[reservations] insert failed: {e}")
        raise HTTPException(status_code=500, detail="db_insert_failed")

    response = {"reservation_id": str(booking_uuid)}

    # Guardar idempotencia (no bloqueante)
    if x_idempotency_key:
        try:
            idem = models.IdempotencyKey(
                key=x_idempotency_key,
                request_hash=body_hash,
                response_json=response,
            )
            db.add(idem); db.commit()
        except Exception as e:
            db.rollback()
            print(f"[reservations] idempotency save failed: {e}")

    # Notificar a POLICÍA en background (tu flujo original)
    bg_payload = {
        "reservation_id": str(booking_uuid),
        "check_in": r.check_in.isoformat(),
        "check_out": r.check_out.isoformat(),
        "guests": r.guests,
        "channel": r.channel,
        "email": r.email_contact,
        "phone": r.phone_contact,
    }
    # Si no quieres notificar en este flujo, comenta la línea siguiente:
    background.add_task(notify_ses_reservation_created, bg_payload)

    return response


# =========================
# 2) Sync externo (si POLICÍA es quien inicia a través de n8n)
#    - Recibe el booking_id generado en POLICÍA
#    - Inserta o reutiliza en GASTOS con ese MISMO UUID
#    - No llama a POLICÍA (ni genera enlaces)
# =========================
class ReservationSyncIn(BaseModel):
    booking_id: UUID
    check_in: date
    check_out: date
    guests: int
    channel: str = "manual"
    email: EmailStr | None = None
    phone: str | None = None

@router.post("/sync", response_model=schemas.ReservationOut)
def sync_reservation_from_police(
    payload: ReservationSyncIn,
    db: Session = Depends(get_db),
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
):
    # Pequeña auth por header (usa ADMIN_KEY para no crear otra env var)
    admin_key = os.getenv("ADMIN_KEY", "")
    if not admin_key or x_internal_key != admin_key:
        raise HTTPException(status_code=403, detail="forbidden")

    # Si ya existe, devolvemos el mismo (idempotente)
    existing = db.query(models.Reservation).get(payload.booking_id)
    if existing:
        return {"reservation_id": str(existing.id)}

    r = models.Reservation(
        id=payload.booking_id,  # usamos el MISMO UUID de POLICÍA
        check_in=payload.check_in,
        check_out=payload.check_out,
        guests=payload.guests,
        channel=payload.channel,
        email_contact=payload.email,
        phone_contact=payload.phone,
    )
    try:
        db.add(r)
        db.commit()
        db.refresh(r)
    except Exception as e:
        db.rollback()
        print(f"[reservations] sync insert failed: {e}")
        raise HTTPException(status_code=500, detail="db_insert_failed")

    return {"reservation_id": str(r.id)}

