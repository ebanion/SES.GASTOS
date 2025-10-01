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
from uuid import UUID
from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr

class ReservationSyncIn(BaseModel):
    booking_id: UUID
    check_in: date
    check_out: date
    guests: int
    channel: str = "manual"
    email: EmailStr | None = None
    phone: Optional[str] = None
