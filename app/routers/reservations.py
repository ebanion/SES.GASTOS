import hashlib, json, uuid
from fastapi import APIRouter, Depends, Header, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from ..services.events import notify_ses_reservation_created

router = APIRouter(prefix="/api/v1/reservations", tags=["reservations"])


def _hash_body(body: dict) -> str:
    # default=str por si entra algún date/datetime
    return hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode("utf-8")).hexdigest()


@router.post("", response_model=schemas.ReservationOut)
def create_reservation(
    payload: schemas.ReservationIn,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
):
    # Compat Pydantic v1/v2
    data_dict = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()

    # Idempotencia simple: misma key + mismo hash => devolvemos misma respuesta
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
            # devolvemos la misma respuesta previa
            return idem.response_json

    # Crear reserva
    r = models.Reservation(
        check_in=payload.check_in,
        check_out=payload.check_out,
        guests=payload.guests,
        channel=payload.channel,
        email_contact=payload.email,
        phone_contact=payload.phone,
    )

    # ---- INSERT con rollback y logging de error ----
    try:
        db.add(r)
        db.commit()
        db.refresh(r)
    except Exception as e:
        db.rollback()
        print(f"[reservations] insert failed: {e}")
        raise HTTPException(status_code=500, detail="db_insert_failed")
    # ------------------------------------------------

    response = {"reservation_id": str(r.id)}

    # Guardar idempotencia (si aplica)
    if x_idempotency_key:
        try:
            idem = models.IdempotencyKey(
                key=x_idempotency_key,
                request_hash=body_hash,
                response_json=response,
            )
            db.add(idem)
            db.commit()
        except Exception as e:
            db.rollback()
            # No rompemos la petición por un fallo al guardar idempotencia
            print(f"[reservations] idempotency save failed: {e}")

    # Publicar evento a POLICÍA (fuego y olvido)
    bg_payload = {
        "reservation_id": str(r.id),
        "check_in": r.check_in.isoformat(),
        "check_out": r.check_out.isoformat(),
        "guests": r.guests,
        "channel": r.channel,
        "email": r.email_contact,
        "phone": r.phone_contact,
    }
    background.add_task(notify_ses_reservation_created, bg_payload)

    return response

