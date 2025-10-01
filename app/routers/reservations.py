import os, hashlib, json, uuid
from fastapi import APIRouter, Depends, Header, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from ..services.events import notify_ses_reservation_created

router = APIRouter(prefix="/api/v1/reservations", tags=["reservations"])

def _hash_body(body: dict) -> str:
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()

@router.post("", response_model=schemas.ReservationOut)
def create_reservation(
    payload: schemas.ReservationIn,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
):
    # Idempotencia simple: misma key + mismo hash => devolvemos misma respuesta
    body_hash = _hash_body(payload.dict())
    if x_idempotency_key:
        idem = db.query(models.IdempotencyKey).filter(models.IdempotencyKey.key == x_idempotency_key).first()
        if idem:
            if idem.request_hash != body_hash:
                raise HTTPException(409, "Idempotency-Key en uso con otro cuerpo")
            return idem.response_json

    # Crear reserva (UUID generado por GASTOS)
    r = models.Reservation(
        check_in=payload.check_in,
        check_out=payload.check_out,
        guests=payload.guests,
        channel=payload.channel,
        email_contact=payload.email,
        phone_contact=payload.phone,
    )
    db.add(r); db.commit(); db.refresh(r)

    response = {"reservation_id": str(r.id)}

    # Guardar idempotencia (si aplica)
    if x_idempotency_key:
        idem = models.IdempotencyKey(
            key=x_idempotency_key,
            request_hash=body_hash,
            response_json=response
        )
        db.add(idem); db.commit()

    # Notificar a SES.HOSPEDAJES en background (fuego y olvido)
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
        x_idempotency_key or str(uuid.uuid4())
    )

    return response

# === NUEVO: crear/forzar una reserva con UUID dado por POLICÍA ===
@router.post("/sync", response_model=schemas.ReservationOut)
def sync_reservation(
    payload: schemas.ReservationSyncIn,
    db: Session = Depends(get_db),
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
):
    # Solo flujos internos (n8n/policía)
    admin = os.getenv("ADMIN_KEY", "")
    if not admin or x_internal_key != admin:
        raise HTTPException(403, "forbidden")

    # Validar UUID y upsert
    rid = uuid.UUID(str(payload.booking_id))

    # Si existe, devolvemos tal cual
    exists = db.query(models.Reservation).filter(models.Reservation.id == rid).first()
    if exists:
        return {"reservation_id": str(exists.id)}

    # Si no existe, lo creamos con ese UUID
    r = models.Reservation(
        id=rid,
        check_in=payload.check_in,
        check_out=payload.check_out,
        guests=payload.guests,
        channel=payload.channel,
        email_contact=payload.email,
        phone_contact=payload.phone,
    )
    db.add(r); db.commit()

    return {"reservation_id": str(rid)}
