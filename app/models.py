# app/models.py
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Date, DateTime, Boolean,
    ForeignKey, Numeric, JSON, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .db import Base

from sqlalchemy import Column, String, Date, DateTime, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID  # solo para 'id'
import uuid
from datetime import datetime, timezone

# ---------- RESERVAS ----------
class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    check_in   = Column(Date, nullable=False)
    check_out  = Column(Date, nullable=False)
    guests     = Column(Integer, nullable=False)
    channel    = Column(String(50))
    email_contact = Column(String(255))
    phone_contact = Column(String(50))
    # NUEVO:
    apartment_id = Column(String(36), ForeignKey("apartments.id"), nullable=True)

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
class Apartment(Base):
    __tablename__ = "apartments"
    # Apartments como String(36), tal y como ya migraste
    id   = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(64), unique=True, nullable=False)
    name = Column(String(255))
    owner_email = Column(String(255))
    is_active   = Column(Boolean, default=True)
    created_at  = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    expenses = relationship("Expense", back_populates="apartment", cascade="all,delete")

# ---------- GASTOS ----------
class Expense(Base):
    __tablename__ = "expenses"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    apartment_id = Column(String(36), ForeignKey("apartments.id"), nullable=False)
    date         = Column(Date, nullable=False)
    amount_gross = Column(Numeric(12, 2), nullable=False)
    currency     = Column(String(3), nullable=False, default="EUR")

    category       = Column(String(50))
    description    = Column(String(500))
    vendor         = Column(String(255))
    invoice_number = Column(String(128), nullable=True)
    source         = Column(String(50), nullable=True)

    vat_rate    = Column(Integer, nullable=True)
    file_url    = Column(String(500), nullable=True)
    status      = Column(String(20), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    apartment = relationship("Apartment", back_populates="expenses")

# ---------- INGRESOS ----------



class Income(Base):
    __tablename__ = "incomes"
    # La columna 'id' puede seguir siendo UUID (en DB es uuid):
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Alineado con DB: ambas varchar(36)
    reservation_id = Column(String(36), ForeignKey("reservations.id"), nullable=True)
    apartment_id   = Column(String(36), ForeignKey("apartments.id"),   nullable=True)

    date = Column(Date, nullable=False)

    amount_gross = Column(Numeric(12, 2), nullable=False)
    currency     = Column(String(3), nullable=False, default="EUR")

    status            = Column(String(20), nullable=False, default="PENDING")  # PENDING | CONFIRMED | CANCELLED
    non_refundable_at = Column(Date, nullable=True)

    source = Column(String(50))

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

