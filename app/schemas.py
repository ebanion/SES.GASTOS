# app/schemas.py
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Literal, List
from pydantic import BaseModel, EmailStr, Field

# ---------- RESERVAS ----------
class ReservationIn(BaseModel):
    check_in: date
    check_out: date
    guests: int = Field(ge=1)
    channel: str = "manual"
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    apartment_id: Optional[str] = None  # VARCHAR(36)

class ReservationSyncIn(BaseModel):
    booking_id: str  # VARCHAR(36) (no UUID aquí)
    check_in: date
    check_out: date
    guests: int = Field(ge=1)
    channel: str = "manual"
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    apartment_id: Optional[str] = None

class ReservationOut(BaseModel):
    reservation_id: str  # devolvemos como string

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
    id: str  # VARCHAR(36)
    code: str
    name: Optional[str] = None
    owner_email: Optional[EmailStr] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

# ---------- GASTOS ----------
class ExpenseIn(BaseModel):
    apartment_id: str  # VARCHAR(36)
    date: date
    amount_gross: Decimal = Field(gt=0)
    currency: str = "EUR"
    category: Optional[str] = None
    description: Optional[str] = None
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    source: Optional[str] = None
    vat_rate: Optional[int] = None
    file_url: Optional[str] = None
    status: Literal["PENDING", "PAID", "CANCELLED"] = "PENDING"

class ExpenseOut(BaseModel):
    id: str           # VARCHAR(36)
    apartment_id: str # VARCHAR(36)
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
class IncomeFromReservationIn(BaseModel):
    reservation_id: str
    amount_gross: Decimal = Field(gt=0)
    currency: str = "EUR"
    policy_days: int = 5  # <- nombre que usa el router
    apartment_id: Optional[str] = None
    source: Optional[str] = "reservation"

class IncomeOut(BaseModel):
    id: str  # UUID expuesto como string
    reservation_id: Optional[str] = None
    apartment_id: Optional[str] = None
    date: date
    amount_gross: Decimal
    currency: str
    status: Literal["PENDING", "CONFIRMED", "CANCELLED"]
    non_refundable_at: Optional[date] = None
    source: Optional[str] = None
    created_at: Optional[datetime] = None

# ---------- DASHBOARD ----------
class ExpenseSummary(BaseModel):
    category: str
    total: float

class DashboardMonthSummary(BaseModel):
    month: int
    incomes_accepted: float = 0.0
    incomes_pending: float = 0.0
    reservations_accepted: int = 0
    reservations_pending: int = 0
    expenses: float = 0.0
    net: float = 0.0
    # opcional: desglose por categorías si lo quieres usar en cards/gráficos
    expenses_by_category: List[ExpenseSummary] = []

class DashboardMonthlyResponse(BaseModel):
    year: int
    items: List[DashboardMonthSummary]


