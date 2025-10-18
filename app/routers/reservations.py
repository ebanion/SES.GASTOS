# app/routers/reservations.py
from __future__ import annotations

import hashlib, json, uuid, traceback
from fastapi import APIRouter, Depends, Header, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from ..db import get_db
from .. import models, schemas
from ..services.events import notify_ses_reservation_created

router = APIRouter(prefix="/api/v1/reservations", tags=["reservations"])


def _hash_body_safe(pyd_model: schemas.ReservationIn) -> str:
    """
    Genera un hash estable del cuerpo. Convierte fechas a ISO con Pydantic v2
    para evitar 'Object of type date is not JSON serializable'.
    """
    try:
        data = pyd_model.model_dump(mode="json")  # fechas -> "YYYY-MM-DD"
    except Exception:
        # último salvavidas
        data = json.loads(pyd_model.model_dump_json())
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def _make_response(reservation_id) -> dict:
    # Siempre devolvemos string para que case con el schema/JSON
    return {"reservation_id": str(reservation_id)}


@router.post("", response_model=schemas.ReservationOut)
def create_reservation(
    payload: schemas.ReservationIn,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
):
    body_hash = _hash_body_safe(payload)

    try:
        # Idempotencia: misma key + mismo hash => misma respuesta
        if x_idempotency_key:
            idem = (
                db.query(models.IdempotencyKey)
                .filter(models.IdempotencyKey.key == x_idempotency_key)
                .first()
            )
            if idem:
                if idem.request_hash != body_hash:
                    raise HTTPException(
                        status_code=409,
                        detail="Idempotency-Key en uso con otro cuerpo",
                    )
                # Asegura forma de respuesta
                if isinstance(idem.response_json, dict) and "reservation_id" in idem.response_json:
                    return idem.response_json
                # Si por lo que sea no está bien guardado, no reinsertamos: devolvemos seguro
                return _make_response(idem.response_json)

        # Crear reserva
        r = models.Reservation(
            check_in=payload.check_in,
            check_out=payload.check_out,
            guests=payload.guests,
            channel=payload.channel,
            email_contact=payload.email,
            phone_contact=payload.phone,
	    apartment_id=payload.apartment_id,
        )
        db.add(r)
        db.commit()
        db.refresh(r)

        response = _make_response(r.id)

        # Guarda registro de idempotencia si nos pasaron clave
        if x_idempotency_key:
            try:
                idem = models.IdempotencyKey(
                    key=x_idempotency_key,
                    request_hash=body_hash,
                    response_json=response,
                )
                db.add(idem)
                db.commit()
            except IntegrityError:
                # carrera: ya existe la clave → no pasa nada
                db.rollback()

        # Disparo a SES.HOSPEDAJES en background (no bloquea la respuesta)
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
            x_idempotency_key or str(uuid.uuid4()),
        )

        return response

    except HTTPException:
        # No toques el estado/rollback para errores ya controlados
        raise
    except (IntegrityError, SQLAlchemyError) as e:
        db.rollback()
        print("[/reservations] DB ERROR:", repr(e))
        traceback.print_exc()
        # detalle con clase de excepción para diagnosticar rápido
        raise HTTPException(status_code=500, detail=f"internal_error:{e.__class__.__name__}")
    except Exception as e:
        db.rollback()
        print("[/reservations] ERROR:", repr(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"internal_error:{e.__class__.__name__}")


# Mantengo el sync que igualaste con POLICÍA
@router.post("/sync", response_model=schemas.ReservationOut)
def sync_reservation(
    payload: schemas.ReservationSyncIn,
    db: Session = Depends(get_db),
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
):
    from os import getenv

    if x_internal_key != getenv("ADMIN_KEY"):
        raise HTTPException(status_code=403, detail="forbidden")

    try:
        r = (
            db.query(models.Reservation)
            .filter(models.Reservation.id == payload.booking_id)
            .first()
        )
        if not r:
            r = models.Reservation(
                id=payload.booking_id,
                check_in=payload.check_in,
                check_out=payload.check_out,
                guests=payload.guests,
                channel=payload.channel,
                email_contact=payload.email,
                phone_contact=payload.phone,
                apartment_id=payload.apartment_id,
            )
            db.add(r)
        else:
            r.check_in = payload.check_in
            r.check_out = payload.check_out
            r.guests = payload.guests
            r.channel = payload.channel
            r.email_contact = payload.email
            r.phone_contact = payload.phone
            r.apartment_id = payload.apartment_id

        db.commit()
        db.refresh(r)
        return _make_response(r.id)

    except (IntegrityError, SQLAlchemyError) as e:
        db.rollback()
        print("[/reservations/sync] DB ERROR:", repr(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"internal_error:{e.__class__.__name__}")
    except Exception as e:
        db.rollback()
        print("[/reservations/sync] ERROR:", repr(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"internal_error:{e.__class__.__name__}")
