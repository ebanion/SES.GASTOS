
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import date
from decimal import Decimal

ExpenseCategory = Literal[
    "internet","limpieza","lavanderia","gas","electricidad",
    "reparaciones","suministros","comisiones","otros"
]

class ApartmentIn(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=120)
    owner_email: Optional[EmailStr] = None
    telegram_chat_id: Optional[str] = None

class ApartmentOut(ApartmentIn):
    id: str

class ExpenseIn(BaseModel):
    apartment_id: str
    date: date
    category: ExpenseCategory
    amount_gross: Decimal
    vat_rate: Decimal = Decimal("21.0")
    currency: str = "EUR"
    vendor: Optional[str] = None
    description: Optional[str] = None
    file_url: Optional[str] = None
    status: Optional[Literal["PENDING","OK"]] = "PENDING"

class ExpenseOut(ExpenseIn):
    id: str

