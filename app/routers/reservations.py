import os, hashlib, json, uuid
from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from ..services.events import notify_ses_reservation_created

router = APIRouter(prefix="/api/v1/reservations", tags=["reservations"])


def _hash_body_safe(body: dict) -> str:
    # Soporta dates/UUIDs sin romper
    return hashlib.sha256(
        json.dumps(body, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


@router.post("", response_model=schemas.ReservationOut)
def create_reservation(
    payload: schemas.ReservationIn,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
):
    # Pydantic v1/v2 compat
    data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()

    # Idempotencia: SOLO si nos pasan cabecera
    body_hash = None
    if x_idempotency_key:
        body_hash = _hash_body_safe(data)
        idem = (
            db.query(models.IdempotencyKey)
            .filter(models.IdempotencyKey.key == x_idempotency_key)
            .first()
        )
        if idem:
            if idem.request_hash != body_hash:
                raise HTTPException(status_code=409, detail="Idempotency-Key en uso con otro cuerpo")
            return idem.response_json

    # Crear reserva (UUID generado aquí)
    r = models.Reservation(
        check_in=payload.check_in,
        check_out=payload.check_out,
        guests=payload.guests,
        channel=payload.channel,
        email_contact=payload.email,
        phone_contact=payload.phone,
    )
    try:
        db.add(r); db.commit(); db.refresh(r)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="db_insert_failed")

    response = {"reservation_id": str(r.id)}

    # Guardar idempotencia (si aplica)
    if x_idempotency_key and body_hash:
        try:
            idem = models.IdempotencyKey(
                key=x_idempotency_key,
                request_hash=body_hash,
                response_json=response,
            )
            db.add(idem); db.commit()
        except Exception:
            db.rollback()  # no rompemos la petición si falla el registro idem

    # Notificar a SES.HOSPEDAJES en background (puedes desactivar si no lo quieres)
    background.add_task(
        notify_ses_reservation_created,
        {
            "reservation_id": str(r.id),
            "check_in": r.check_in.isoformat(),
            "check_out": r.check_out.isoformat(),
            "guests": r.guests,
            "channel": r.channel,
            "email": r.email_contact,
            "phone": r.phone_contact,
        },
    )

    return response


# === /sync: inserta/usa el MISMO UUID que generó POLICÍA ===
@router.post("/sync", response_model=schemas.ReservationOut)
def sync_reservation_from_police(
    payload: schemas.ReservationSyncIn,
    db: Session = Depends(get_db),
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
):
    admin_key = os.getenv("ADMIN_KEY", "")
    if not admin_key or x_internal_key != admin_key:
        raise HTTPException(status_code=403, detail="forbidden")

    # Validar/normalizar UUID externo
    rid = uuid.UUID(str(payload.booking_id))

    # Idempotente: si ya existe, devolvemos el mismo
    existing = db.query(models.Reservation).get(rid)
    if existing:
        return {"reservation_id": str(existing.id)}

    r = models.Reservation(
        id=rid,
        check_in=payload.check_in,
        check_out=payload.check_out,
        guests=payload.guests,
        channel=payload.channel,
        email_contact=payload.email,
        phone_contact=payload.phone,
    )
    try:
        db.add(r); db.commit(); db.refresh(r)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="db_insert_failed")

    return {"reservation_id": str(r.id)}
