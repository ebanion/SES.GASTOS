# app/schemas.py
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID
from decimal import Decimal
from typing import Optional, Literal

from pydantic import BaseModel, EmailStr


# ---------- RESERVAS ----------
class ReservationIn(BaseModel):
    check_in: date
    check_out: date
    guests: int
    channel: str = "manual"
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class ReservationOut(BaseModel):
    reservation_id: UUID


class ReservationSyncIn(BaseModel):
    """Usado por /api/v1/reservations/sync cuando POLICÍA ya generó el UUID."""
    booking_id: UUID
    check_in: date
    check_out: date
    guests: int
    channel: str = "manual"
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


# ---------- APARTAMENTOS ----------
class ApartmentCreate(BaseModel):
    code: str
    name: Optional[str] = None
    owner_email: Optional[EmailStr] = None


class ApartmentOut(BaseModel):
    id: UUID
    code: str
    name: Optional[str] = None
    owner_email: Optional[EmailStr] = None
    is_active: bool = True
    created_at: Optional[datetime] = None


# ---------- GASTOS ----------
class ExpenseIn(BaseModel):
    apartment_id: UUID
    date: date
    category: Optional[str] = None
    vendor: Optional[str] = None
    description: Optional[str] = None
    currency: str = "EUR"
    amount_gross: Decimal
    vat_rate: Optional[int] = None
    file_url: Optional[str] = None
    status: Literal["PENDING", "PAID", "CANCELLED"] = "PENDING"


class ExpenseOut(ExpenseIn):
    id: UUID
