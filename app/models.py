# --- NUEVO: Apartamentos y Gastos ---
from sqlalchemy import Column, String, Text, Date, Numeric, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship
import uuid

def _uuid():
    return str(uuid.uuid4())

class Apartment(Base):
    __tablename__ = "apartments"
    id = Column(String(36), primary_key=True, default=_uuid)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(120), nullable=False)
    owner_email = Column(String(200), nullable=True)
    telegram_chat_id = Column(String(64), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(String(32), nullable=False, default=lambda: func.now())
    expenses = relationship("Expense", back_populates="apartment", cascade="all, delete-orphan")

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(String(36), primary_key=True, default=_uuid)
    apartment_id = Column(String(36), ForeignKey("apartments.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    category = Column(String(32), nullable=False)
    vendor = Column(String(120), nullable=True)
    description = Column(Text, nullable=True)
    currency = Column(String(3), nullable=False, default="EUR")
    amount_gross = Column(Numeric(12, 2), nullable=False)
    vat_rate = Column(Numeric(5, 2), nullable=False, default=21.00)
    file_url = Column(Text, nullable=True)
    status = Column(String(16), nullable=False, default="PENDING")
    created_at = Column(String(32), nullable=False, default=lambda: func.now())
    apartment = relationship("Apartment", back_populates="expenses")
    created_at = Column(String(32), nullable=False, default=lambda: func.now())
    apartment = relationship("Apartment", back_populates="expenses")

