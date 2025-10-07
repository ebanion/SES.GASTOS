# app/routers/apartments.py
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
import os

from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/v1/apartments", tags=["apartments"])

def require_internal_key(
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key")
):
    if x_internal_key != os.getenv("ADMIN_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden")

@router.post(
    "",
    response_model=schemas.ApartmentOut,
    dependencies=[Depends(require_internal_key)],
)
def create_apartment(payload: schemas.ApartmentCreate, db: Session = Depends(get_db)):
    code = payload.code.strip()
    name = (payload.name or "").strip()
    owner = (payload.owner_email or None)

    # --- UPSERT nativo Postgres: si existe code -> no hace nada; si no -> inserta
    try:
        stmt = (
            pg_insert(models.Apartment)
            .values(code=code, name=name, owner_email=owner, is_active=True)
            .on_conflict_do_nothing(index_elements=[models.Apartment.code])
            .returning(models.Apartment.id)
        )
        row = db.execute(stmt).first()  # Row | None
        if row is None:
            # Ya existía: devolver el existente (idempotente)
            apt = db.execute(
                select(models.Apartment).where(models.Apartment.code == code)
            ).scalar_one()
        else:
            db.commit()
            apt_id = row[0]
            apt = db.query(models.Apartment).filter_by(id=apt_id).first()
        return apt

    except Exception as e:
        # Fallback genérico (por si no estamos en Postgres o algo raro)
        db.rollback()
        try:
            existing = db.query(models.Apartment).filter(models.Apartment.code == code).first()
            if existing:
                return existing
            apt = models.Apartment(code=code, name=name, owner_email=owner, is_active=True)
            db.add(apt); db.commit(); db.refresh(apt)
            return apt
        except IntegrityError as ie:
            db.rollback()
            existing = db.query(models.Apartment).filter(models.Apartment.code == code).first()
            if existing:
                return existing
            print(f"[apartments] IntegrityError: {ie}")
            raise HTTPException(status_code=500, detail="integrity_error")
        except Exception as e2:
            db.rollback()
            print(f"[apartments] unexpected: {e2}")
            raise HTTPException(status_code=500, detail="unexpected_error")

@router.get("", response_model=list[schemas.ApartmentOut])
def list_apartments(db: Session = Depends(get_db)):
    return (
        db.query(models.Apartment)
        .order_by(models.Apartment.created_at.desc())
        .all()
    )

