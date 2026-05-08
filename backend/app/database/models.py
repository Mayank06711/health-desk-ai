from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship, DeclarativeBase
from pydantic import BaseModel


# ---- SQLAlchemy ORM Models ----

class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    appointments = relationship("AppointmentModel", back_populates="user")


class SlotModel(Base):
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False)   # "2026-05-12"
    time = Column(String(5), nullable=False)     # "14:00"
    is_available = Column(Boolean, default=True)

    __table_args__ = (UniqueConstraint("date", "time", name="uq_slot_date_time"),)

    appointments = relationship("AppointmentModel", back_populates="slot")


class AppointmentModel(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=False)
    status = Column(String(20), default="booked")  # booked | cancelled
    booked_at = Column(DateTime, default=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)

    user = relationship("UserModel", back_populates="appointments")
    slot = relationship("SlotModel", back_populates="appointments")

    __table_args__ = (
        Index("idx_appointments_user_id", "user_id"),
        Index("idx_appointments_status", "status"),
    )


class CallSummaryModel(Base):
    __tablename__ = "call_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_phone = Column(String(20), nullable=True)
    summary = Column(String, nullable=False)
    appointments_json = Column(String, nullable=True)
    preferences_json = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---- Pydantic Schemas (for serialization) ----

class User(BaseModel):
    id: int
    phone: str
    name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class Slot(BaseModel):
    id: int
    date: str
    time: str
    is_available: bool

    model_config = {"from_attributes": True}


class Appointment(BaseModel):
    id: int
    user: User
    slot: Slot
    status: str
    booked_at: datetime

    model_config = {"from_attributes": True}


class CallSummary(BaseModel):
    summary: str
    appointments: list[dict]
    preferences: list[str]
    timestamp: str
