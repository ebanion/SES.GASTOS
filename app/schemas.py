# app/schemas.py
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Literal, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
import re

# ---------- CUENTAS DE ANFITRIÓN ----------
class AccountCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    contact_email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None

    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('El nombre de la cuenta no puede estar vacío')
        return v.strip()

class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    contact_email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    is_active: Optional[bool] = None
    max_apartments: Optional[int] = Field(None, ge=1, le=1000)

class AccountOut(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    is_active: bool
    subscription_status: str
    max_apartments: int
    contact_email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    tax_id: Optional[str]
    trial_ends_at: Optional[datetime]
    subscription_ends_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Estadísticas (se calculan dinámicamente)
    apartments_count: Optional[int] = None
    users_count: Optional[int] = None

    class Config:
        from_attributes = True

# ---------- USUARIOS ----------
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=6)
    phone: Optional[str] = None
    timezone: str = "Europe/Madrid"
    language: str = "es"

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    is_active: Optional[bool] = None

class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    is_superadmin: bool
    phone: Optional[str]
    avatar_url: Optional[str]
    timezone: str
    language: str
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True

# ---------- MEMBRESÍAS DE CUENTA ----------
class AccountUserCreate(BaseModel):
    user_email: EmailStr  # Se busca el usuario por email
    role: Literal["owner", "admin", "member", "viewer"] = "member"
    permissions: Optional[Dict[str, Any]] = None

class AccountUserUpdate(BaseModel):
    role: Optional[Literal["owner", "admin", "member", "viewer"]] = None
    is_active: Optional[bool] = None
    permissions: Optional[Dict[str, Any]] = None

class AccountUserOut(BaseModel):
    id: str
    account_id: str
    user_id: str
    role: str
    is_active: bool
    permissions: Optional[Dict[str, Any]]
    created_at: datetime
    
    # Datos del usuario (join)
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None

    class Config:
        from_attributes = True

# ---------- AUTENTICACIÓN CON CUENTAS ----------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    accounts: List[AccountOut]  # Cuentas a las que pertenece
    default_account_id: Optional[str] = None

class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=6)
    account_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = None

    @validator('account_name')
    def validate_account_name(cls, v):
        if not v.strip():
            raise ValueError('El nombre de la cuenta no puede estar vacío')
        return v.strip()

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

class IncomeCreate(BaseModel):
    """Schema para crear ingresos manualmente"""
    reservation_id: Optional[str] = None
    apartment_id: str
    date: date
    amount_gross: Decimal = Field(gt=0)
    currency: str = "EUR"
    status: Optional[Literal["PENDING", "CONFIRMED", "CANCELLED"]] = "PENDING"
    non_refundable_at: Optional[date] = None
    source: Optional[str] = "manual"
    guest_name: Optional[str] = None
    guest_email: Optional[str] = None
    booking_reference: Optional[str] = None
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    guests_count: Optional[int] = None

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

# ---------- USUARIOS ----------
class UserBase(BaseModel):
    email: str
    full_name: str
    phone: Optional[str] = None
    company: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserOutLegacy(UserBase):
    id: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# ---------- ANALYTICS FINANCIEROS ----------
class KPIsOut(BaseModel):
    """KPIs hoteleros principales"""
    adr: float  # Average Daily Rate
    occupancy_rate: float  # % ocupación
    revpar: float  # Revenue Per Available Room
    period_start: str
    period_end: str
    apartment_id: Optional[str] = None

class FinancialHealthOut(BaseModel):
    """Estado de salud financiera"""
    status: Literal["green", "yellow", "red"]
    score: int  # 0-100
    margin_percent: float
    occupancy_rate: float
    expense_ratio: float
    total_income: float
    total_expenses: float
    net_profit: float
    message: str
    period_days: int
    start_date: str
    end_date: str

class YearOverYearOut(BaseModel):
    """Comparativa año actual vs anterior"""
    current_period: Dict[str, Any]
    previous_period: Dict[str, Any]
    variations: Dict[str, float]

class ExpenseCategoryAnalysis(BaseModel):
    """Análisis de gasto por categoría"""
    category: str
    total_amount: float
    transaction_count: int
    percent_of_income: float
    benchmark_percent: float
    status: Literal["optimal", "high", "very_high"]
    recommendation: str

# ---------- FISCAL ----------
class QuarterlyIVAOut(BaseModel):
    """Cálculo IVA trimestral"""
    year: int
    quarter: int
    quarter_label: str
    start_date: str
    end_date: str
    total_income: float
    total_expenses: float
    iva_repercutido: float
    iva_soportado: float
    iva_to_pay: float
    iva_rate_percent: float
    due_date: str
    days_until_due: int
    is_overdue: bool
    status: str

class QuarterlyIRPFOut(BaseModel):
    """Cálculo IRPF trimestral"""
    year: int
    quarter: int
    quarter_label: str
    regime: str
    start_date: str
    end_date: str
    total_income: float
    total_expenses: float
    net_income: float
    irpf_base: float
    irpf_rate_percent: float
    irpf_calculated: float
    previous_payments: float
    quarterly_payment: float
    due_date: str
    days_until_due: int
    is_overdue: bool

class FiscalAlertOut(BaseModel):
    """Alerta fiscal"""
    type: str  # deadline, threshold, data_quality, planning, optimization
    severity: str  # info, warning, error, success
    title: str
    message: str
    icon: str
    due_date: Optional[str] = None
    amount: Optional[float] = None
    threshold: Optional[float] = None
    count: Optional[int] = None
    action_url: Optional[str] = None

class TaxScenarioOut(BaseModel):
    """Simulación de escenarios fiscales"""
    projected_annual_income: float
    projected_annual_expenses: float
    projected_net_income: float
    scenarios: Dict[str, Any]
    recommendation: str


