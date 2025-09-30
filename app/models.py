import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Integer, Date, DateTime, JSON, Enum, UniqueConstraint, Index, Text
)
from sqlalchemy.dialects.postgresql import UUID
from .db import Base

class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    check_in = Column(Date, nullable=False)
    check_out = Column(Date, nullable=False)
    guests = Column(Integer, nullable=False)
    channel = Column(String(40), default="manual")
    email_contact = Column(String(180))
    phone_contact = Column(String(60))
    status = Column(String(20), default="CREATED")  # CREATED | CONFIRMED | CANCELLED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_res_checkin", "check_in"),
    )

class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    key = Column(String(80), primary_key=True)
    request_hash = Column(String(64), nullable=False)
    response_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(60), nullable=False)  # e.g., ReservationCreated
    payload = Column(JSON, nullable=False)
    status = Column(String(20), default="PENDING")  # PENDING | SENT | FAILED
    tries = Column(Integer, default=0, nullable=False)
    last_error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
