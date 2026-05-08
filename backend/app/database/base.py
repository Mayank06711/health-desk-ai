from abc import ABC, abstractmethod
from app.database.models import User, Slot, Appointment


class DatabaseBase(ABC):

    @abstractmethod
    async def initialize(self) -> None:
        """Create tables and seed data if empty."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close connection pool."""
        ...

    # ---- User operations ----

    @abstractmethod
    async def find_user_by_phone(self, phone: str) -> User | None:
        ...

    @abstractmethod
    async def create_user(self, phone: str, name: str | None = None) -> User:
        ...

    @abstractmethod
    async def update_user_name(self, phone: str, name: str) -> User:
        ...

    # ---- Slot operations ----

    @abstractmethod
    async def get_available_slots(self) -> list[Slot]:
        ...

    @abstractmethod
    async def get_slot(self, date: str, time: str) -> Slot | None:
        ...

    # ---- Appointment operations ----

    @abstractmethod
    async def create_appointment(self, user_id: int, slot_id: int) -> Appointment:
        ...

    @abstractmethod
    async def get_user_appointments(self, phone: str) -> list[Appointment]:
        ...

    @abstractmethod
    async def cancel_appointment(self, appointment_id: int) -> bool:
        ...

    @abstractmethod
    async def find_appointment(self, phone: str, date: str, time: str) -> Appointment | None:
        ...

    # ---- Summary operations ----

    @abstractmethod
    async def save_call_summary(
        self, user_phone: str, summary: str, appointments_json: str, preferences_json: str
    ) -> None:
        ...
