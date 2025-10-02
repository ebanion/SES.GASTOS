# app/models.py
from __future__ import annotations

import uuid
from sqlalchemy import (
    Column, String, Integer, Date, DateTime, Boolean,
    ForeignKey, Numeric, JSON, func
)
from sqlalchemy.orm import relationship
from .db import Base


# ---------- RESERVAS ----------
class Reservation(Base):
    __tablename__ = "reservations"

    # guardamos UUID como texto para máxima compatibilidad
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    check_in   = Column(Date, nullable=False)
    check_out  = Column(Date, nullable=False)
    guests     = Column(Integer, nullable=False)
    channel    = Column(String(50), nullable=True)
    email_contact = Column(String(255), nullable=True)
    phone_contact = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ---------- IDEMPOTENCIA ----------
class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    key          = Column(String(128), primary_key=True)
    request_hash = Column(String(64), nullable=False)
    response_json = Column(JSON, nullable=False)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())


# ---------- APARTAMENTOS ----------
class Apartment(Base):
    __tablename__ = "apartments"

    id   = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(64), unique=True, nullable=False)
    name = Column(String(255), nullable=True)

    owner_email = Column(String(255), nullable=True)
    is_active   = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # relación 1-N con gastos
    expenses = relationship("Expense", back_populates="apartment", cascade="all,delete")


# ---------- GASTOS ----------
class Expense(Base):
    __tablename__ = "expenses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    apartment_id = Column(String(36), ForeignKey("apartments.id"), nullable=False)
    date     = Column(Date, nullable=False)
    amount   = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")

    category    = Column(String(50), nullable=True)   # internet, limpieza, etc.
    description = Column(String(500), nullable=True)
    vendor      = Column(String(255), nullable=True)
    invoice_number = Column(String(128), nullable=True)
    source      = Column(String(50), nullable=True)   # telegram, email, manual

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    apartment = relationship("Apartment", back_populates="expenses")

