from app.database.base import DatabaseBase
from app.database.models import User, Slot, Appointment
from app.logger import logger


class AppointmentService:

    def __init__(self, db: DatabaseBase):
        self._db = db

    async def identify_user(self, phone: str) -> dict:
        """Find or create user by phone number."""
        user = await self._db.find_user_by_phone(phone)
        if user:
            appts = await self._db.get_user_appointments(phone)
            logger.info(f"User found: phone={phone}, name={user.name}, appointments={len(appts)}")
            return {"found": True, "user": user, "appointment_count": len(appts)}

        user = await self._db.create_user(phone=phone)
        logger.info(f"New user created: phone={phone}")
        return {"found": False, "user": user, "appointment_count": 0}

    async def update_user_name(self, phone: str, name: str) -> User:
        return await self._db.update_user_name(phone, name)

    async def get_available_slots(self) -> list[Slot]:
        slots = await self._db.get_available_slots()
        logger.info(f"Available slots: {len(slots)}")
        return slots

    async def book_appointment(self, phone: str, date: str, time: str, name: str | None = None) -> dict:
        """Book an appointment with validation."""
        user = await self._db.find_user_by_phone(phone)
        if not user:
            return {"success": False, "message": "User not found. Please identify first.", "appointment": None}

        if name and not user.name:
            await self._db.update_user_name(phone, name)

        slot = await self._db.get_slot(date, time)
        if not slot:
            return {"success": False, "message": f"No slot exists for {date} at {time}.", "appointment": None}

        if not slot.is_available:
            return {"success": False, "message": f"Slot {date} at {time} is already booked.", "appointment": None}

        try:
            appointment = await self._db.create_appointment(user_id=user.id, slot_id=slot.id)
            logger.info(f"Appointment booked: {phone} -> {date} {time}")
            return {"success": True, "message": f"Appointment booked for {date} at {time}.", "appointment": appointment}
        except ValueError as e:
            return {"success": False, "message": str(e), "appointment": None}

    async def get_user_appointments(self, phone: str) -> list[Appointment]:
        return await self._db.get_user_appointments(phone)

    async def cancel_appointment(self, phone: str, date: str, time: str) -> dict:
        """Cancel an appointment by phone + date + time."""
        appointment = await self._db.find_appointment(phone, date, time)
        if not appointment:
            return {"success": False, "message": f"No appointment found for {date} at {time}."}

        cancelled = await self._db.cancel_appointment(appointment.id)
        if cancelled:
            logger.info(f"Appointment cancelled: {phone} -> {date} {time}")
            return {"success": True, "message": f"Appointment on {date} at {time} has been cancelled."}
        return {"success": False, "message": "Failed to cancel appointment."}

    async def modify_appointment(
        self, phone: str, old_date: str, old_time: str, new_date: str, new_time: str
    ) -> dict:
        """Modify by cancelling old and booking new."""
        # Check old appointment exists
        old_appt = await self._db.find_appointment(phone, old_date, old_time)
        if not old_appt:
            return {"success": False, "message": f"No appointment found for {old_date} at {old_time}.", "appointment": None}

        # Check new slot is available
        new_slot = await self._db.get_slot(new_date, new_time)
        if not new_slot:
            return {"success": False, "message": f"No slot exists for {new_date} at {new_time}.", "appointment": None}
        if not new_slot.is_available:
            return {"success": False, "message": f"Slot {new_date} at {new_time} is already booked.", "appointment": None}

        # Cancel old
        await self._db.cancel_appointment(old_appt.id)

        # Book new
        user = await self._db.find_user_by_phone(phone)
        appointment = await self._db.create_appointment(user_id=user.id, slot_id=new_slot.id)

        logger.info(f"Appointment modified: {phone} -> {old_date} {old_time} => {new_date} {new_time}")
        return {
            "success": True,
            "message": f"Appointment moved from {old_date} {old_time} to {new_date} {new_time}.",
            "appointment": appointment,
        }
