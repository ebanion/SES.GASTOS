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
    guest_name = Column(String(255), nullable=True)

    # VINCULACIÓN CON APARTAMENTO (que ya está vinculado a cuenta)
    apartment_id = Column(String(36), ForeignKey("apartments.id"), nullable=False)
    
    # Status para el dashboard: PENDING, CONFIRMED, CANCELLED
    status = Column(String(20), nullable=False, default="CONFIRMED")
    
    # Datos adicionales
    booking_reference = Column(String(100), nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="EUR")
    
    # Notas internas
    notes = Column(String(1000), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    apartment = relationship("Apartment", back_populates="reservations")

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
    code = Column(String(64), nullable=False)  # Único dentro de la cuenta
    name = Column(String(255))
    description = Column(String(500), nullable=True)
    
    # VINCULACIÓN CON CUENTA (TENANT)
    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    
    # Datos del apartamento
    address = Column(String(500), nullable=True)
    max_guests = Column(Integer, nullable=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    
    # Estado y configuración
    is_active = Column(Boolean, default=True)
    
    # Campos legacy (mantener por compatibilidad)
    owner_email = Column(String(255), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # Deprecated
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    account = relationship("Account", back_populates="apartments")
    expenses = relationship("Expense", back_populates="apartment", cascade="all,delete")
    incomes = relationship("Income", back_populates="apartment", cascade="all,delete")
    reservations = relationship("Reservation", back_populates="apartment", cascade="all,delete")
    
    # Legacy relationship (mantener por compatibilidad)
    user = relationship("User", foreign_keys=[user_id])

    # Constraint único: código único dentro de cada cuenta
    __table_args__ = (
        {"extend_existing": True},
    )

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
    source            = Column(String(50))  # BOOKING, AIRBNB, WEB, MANUAL
    
    # Nuevos campos para gestión de reservas por email
    guest_name = Column(String(255), nullable=True)
    guest_email = Column(String(255), nullable=True)
    booking_reference = Column(String(100), nullable=True)
    check_in_date = Column(Date, nullable=True)
    check_out_date = Column(Date, nullable=True)
    guests_count = Column(Integer, nullable=True)
    
    # Para tracking de emails procesados
    email_message_id = Column(String(255), nullable=True, unique=True)
    processed_from_email = Column(Boolean, default=False)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    apartment = relationship("Apartment", back_populates="incomes")
    reservation = relationship("Reservation")


# ---------- CUENTAS DE ANFITRIÓN (TENANTS) ----------
class Account(Base):
    """
    Cuenta de anfitrión/gestor - Tenant principal del sistema SaaS
    Cada cuenta es completamente independiente
    """
    __tablename__ = "accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)  # "Apartamentos Playa S.L."
    slug = Column(String(100), unique=True, nullable=False)  # "apartamentos-playa"
    description = Column(String(500), nullable=True)
    
    # Configuración de la cuenta
    is_active = Column(Boolean, default=True)
    subscription_status = Column(String(20), default="trial")  # trial, active, suspended, cancelled
    max_apartments = Column(Integer, default=10)  # Límite por plan
    
    # Datos de contacto/facturación
    contact_email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    tax_id = Column(String(50), nullable=True)  # CIF/NIF
    
    # Fechas importantes
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    subscription_ends_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    account_users = relationship("AccountUser", back_populates="account", cascade="all,delete")
    apartments = relationship("Apartment", back_populates="account", cascade="all,delete")

# ---------- USUARIOS DEL SISTEMA ----------
class User(Base):
    """
    Usuario individual - puede pertenecer a múltiples cuentas
    """
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Superadministrador del sistema (tú)
    is_superadmin = Column(Boolean, default=False)
    
    # Datos personales
    phone = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    timezone = Column(String(50), default="Europe/Madrid")
    language = Column(String(5), default="es")
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relaciones
    account_memberships = relationship("AccountUser", back_populates="user", foreign_keys="AccountUser.user_id", cascade="all,delete")

# ---------- RELACIÓN USUARIO-CUENTA (MEMBRESÍAS) ----------
class AccountUser(Base):
    """
    Relación muchos-a-muchos entre usuarios y cuentas con roles
    Un usuario puede estar en varias cuentas, cada una con un rol diferente
    """
    __tablename__ = "account_users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Roles dentro de la cuenta
    role = Column(String(20), nullable=False, default="member")  # owner, admin, member, viewer
    
    # Estado de la membresía
    is_active = Column(Boolean, default=True)
    invited_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    invitation_accepted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Permisos específicos (JSON para flexibilidad)
    permissions = Column(JSON, nullable=True)
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    account = relationship("Account", back_populates="account_users")
    user = relationship("User", back_populates="account_memberships", foreign_keys=[user_id])
    invited_by_user = relationship("User", foreign_keys=[invited_by], post_update=True)

    # Constraint único: un usuario solo puede tener un rol por cuenta
    __table_args__ = (
        {"extend_existing": True},
    )