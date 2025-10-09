# app/schemas.py
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ---------- RESERVAS ----------
class ReservationIn(BaseModel):
    check_in: date
    check_out: date
    guests: int = Field(ge=1)
    channel: str = "manual"
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    # NUEVO:
    apartment_id: Optional[str] = None  # String(36)

class ReservationSyncIn(BaseModel):
    booking_id: UUID
    check_in: date
    check_out: date
    guests: int = Field(ge=1)
    channel: str = "manual"
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    # NUEVO:
    apartment_id: Optional[str] = None

# ---------- APARTAMENTOS ----------
class ApartmentCreate(BaseModel):
    code: str
    name: Optional[str] = None
    owner_email: Optional[EmailStr] = None


class ApartmentUpdate(BaseModel):
    name: Optional[str] = None
    owner_email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


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
    amount_gross: Decimal = Field(gt=0)
    currency: str = "EUR"
    category: Optional[str] = None
    description: Optional[str] = None
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    source: Optional[str] = None
    # si ya tienes columnas extras en DB:
    vat_rate: Optional[int] = None
    file_url: Optional[str] = None
    status: Literal["PENDING", "PAID", "CANCELLED"] = "PENDING"


class ExpenseOut(BaseModel):
    id: UUID
    apartment_id: UUID
    date: date
    amount_gross: Decimal
    currency: str
    category: Optional[str] = None
    description: Optional[str] = None
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    source: Optional[str] = None
    vat_rate: Optional[int] = None
    file_url: Optional[str] = None
    status: Optional[str] = None

# ---------- INGRESOS ----------
from typing import Literal
from pydantic import BaseModel, Field
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal

class IncomeFromReservationIn(BaseModel):
    reservation_id: UUID
    amount_gross: Decimal = Field(gt=0)
    currency: str = "EUR"
    # días de cancelación gratuita (si 5 => no reembolsable 5 días antes de check_in)
    non_refundable_days: int = 5
    # opcional por ahora (a futuro se puede guardar apartment_id dentro de Reservation)
    apartment_id: str | None = None
    source: str | None = "reservation"

class IncomeOut(BaseModel):
    id: UUID
    reservation_id: UUID | None = None
    apartment_id: str | None = None
    date: date
    amount_gross: Decimal
    currency: str
    status: Literal["PENDING", "CONFIRMED", "CANCELLED"]
    non_refundable_at: date | None = None
    source: str | None = None
    created_at: datetime | None = None

