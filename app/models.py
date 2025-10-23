# app/models.py
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Date, DateTime, Boolean,
    ForeignKey, Numeric, JSON, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .db import Base

# ---------- RESERVAS ----------
class Reservation(Base):
    __tablename__ = "reservations"

    # VARCHAR(36) alineado con migraciones
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    check_in   = Column(Date, nullable=False)
    check_out  = Column(Date, nullable=False)
    guests     = Column(Integer, nullable=False)
    channel    = Column(String(50))
    email_contact = Column(String(255))
    phone_contact = Column(String(50))

    # Puede ser nulo (no siempre se asigna al crear)
    apartment_id = Column(String(36), ForeignKey("apartments.id"), nullable=True)
    
    # Status para el dashboard: PENDING, CONFIRMED, CANCELLED
    status = Column(String(20), nullable=False, default="CONFIRMED")

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

    id   = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(64), unique=True, nullable=False)
    name = Column(String(255))
    owner_email = Column(String(255))
    is_active   = Column(Boolean, default=True)
    
    # Relación con usuario
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    created_at  = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    expenses = relationship("Expense", back_populates="apartment", cascade="all,delete")
    user = relationship("User", back_populates="apartments")

# ---------- GASTOS ----------
class Expense(Base):
    __tablename__ = "expenses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    apartment_id = Column(String(36), ForeignKey("apartments.id"), nullable=False)
    date         = Column(Date, nullable=False)

    # En BD la columna es amount_gross (numeric(12,2))
    amount_gross = Column(Numeric(12, 2), nullable=False)
    currency     = Column(String(3), nullable=False, default="EUR")

    category       = Column(String(50))         # nullable en código; BD puede exigirlo
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

    # PK UUID (se queda como uuid en BD)
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Alineado con reservations.id (varchar(36))
    reservation_id = Column(String(36), ForeignKey("reservations.id"), nullable=True)

    # Alineado con apartments.id (varchar(36))
    apartment_id   = Column(String(36), ForeignKey("apartments.id"),   nullable=True)

    date = Column(Date, nullable=False)

    amount_gross = Column(Numeric(12, 2), nullable=False)
    currency     = Column(String(3), nullable=False, default="EUR")

    status            = Column(String(20), nullable=False, default="PENDING")  # PENDING | CONFIRMED | CANCELLED
    non_refundable_at = Column(Date, nullable=True)
    source            = Column(String(50))

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Código para añadir al final de models.py

# ---------- USUARIOS ----------
class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    phone = Column(String(50), nullable=True)
    company = Column(String(255), nullable=True)
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relación con apartamentos
    apartments = relationship("Apartment", back_populates="user", cascade="all,delete")