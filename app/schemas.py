from datetime import date
from pydantic import BaseModel, EmailStr
from typing import Optional

class ReservationIn(BaseModel):
    check_in: date
    check_out: date
    guests: int
    channel: str = "manual"
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class ReservationOut(BaseModel):
    reservation_id: str
