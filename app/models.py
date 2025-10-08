# app/models.py
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Date, DateTime, Boolean,
    ForeignKey, Numeric, JSON, func
)
from sqlalchemy.orm import relationship
from .db import Base

# ---------- RESERVAS ----------
class Reservation(Base):
    __tablename__ = "reservations"
    # En reservations tu columna id ya es UUID en DB; si allí ya funciona, no lo tocamos
    from sqlalchemy.dialects.postgresql import UUID as PGUUID
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    check_in   = Column(Date, nullable=False)
    check_out  = Column(Date, nullable=False)
    guests     = Column(Integer, nullable=False)
    channel    = Column(String(50))
    email_contact = Column(String(255))
    phone_contact = Column(String(50))
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

# ---------- IDEMPOTENCIA ----------
class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    key           = Column(String(128), primary_key=True)
    request_hash  = Column(String(64), nullable=False)
    response_json = Column(JSON, nullable=False)
    created_at    = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

# ---------- APARTAMENTOS ----------
# IMPORTANTE: en DB 'id' es VARCHAR(36), así que aquí lo alineamos a String(36)
class Apartment(Base):
    __tablename__ = "apartments"
    id   = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(64), unique=True, nullable=False)
    name = Column(String(255))
    owner_email = Column(String(255))
    is_active   = Column(Boolean, default=True)
    created_at  = Column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
    )
    expenses = relationship("Expense", back_populates="apartment", cascade="all,delete")

# ---------- GASTOS ----------
# También alineamos el FK a String(36) para que case con apartments.id
class Expense(Base):
    __tablename__ = "expenses"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    apartment_id = Column(String(36), ForeignKey("apartments.id"), nullable=False)
    date     = Column(Date, nullable=False)
    amount   = Column(Numeric(12, 2), nullable=False)  # mapea amount_gross del schema
    currency = Column(String(3), nullable=False, default="EUR")

    category       = Column(String(50))
    description    = Column(String(500))
    vendor         = Column(String(255))
    invoice_number = Column(String(128))
    source         = Column(String(50))

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    apartment = relationship("Apartment", back_populates="expenses")

