from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.database.base import DatabaseBase
from app.database.models import (
    Base, UserModel, SlotModel, AppointmentModel, CallSummaryModel,
    User, Slot, Appointment,
)
from app.database.seed import generate_slots
from app.logger import logger


class PostgresDatabase(DatabaseBase):

    def __init__(self, database_url: str):
        self._engine = create_async_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            echo=False,
        )
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

    async def initialize(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")

        # Seed slots if empty
        async with self._session_factory() as session:
            result = await session.execute(select(SlotModel).limit(1))
            if result.scalar_one_or_none() is None:
                slots = generate_slots()
                session.add_all(slots)
                await session.commit()
                logger.info(f"Seeded {len(slots)} appointment slots")

    async def close(self) -> None:
        await self._engine.dispose()
        logger.info("Database connections closed")

    # ---- User operations ----

    async def find_user_by_phone(self, phone: str) -> User | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.phone == phone)
            )
            row = result.scalar_one_or_none()
            return User.model_validate(row) if row else None

    async def create_user(self, phone: str, name: str | None = None) -> User:
        async with self._session_factory() as session:
            user = UserModel(phone=phone, name=name)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info(f"Created user: phone={phone}")
            return User.model_validate(user)

    async def update_user_name(self, phone: str, name: str) -> User:
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.phone == phone)
            )
            user = result.scalar_one_or_none()
            if not user:
                raise ValueError(f"User not found: {phone}")
            user.name = name
            await session.commit()
            await session.refresh(user)
            logger.info(f"Updated user name: phone={phone}, name={name}")
            return User.model_validate(user)

    # ---- Slot operations ----

    async def get_available_slots(self) -> list[Slot]:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        async with self._session_factory() as session:
            result = await session.execute(
                select(SlotModel)
                .where(and_(SlotModel.is_available == True, SlotModel.date >= today))
                .order_by(SlotModel.date, SlotModel.time)
            )
            rows = result.scalars().all()
            return [Slot.model_validate(r) for r in rows]

    async def get_slot(self, date: str, time: str) -> Slot | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(SlotModel).where(
                    and_(SlotModel.date == date, SlotModel.time == time)
                )
            )
            row = result.scalar_one_or_none()
            return Slot.model_validate(row) if row else None

    # ---- Appointment operations ----

    async def create_appointment(self, user_id: int, slot_id: int) -> Appointment:
        async with self._session_factory() as session:
            # Mark slot as unavailable
            result = await session.execute(
                select(SlotModel).where(
                    and_(SlotModel.id == slot_id, SlotModel.is_available == True)
                )
            )
            slot = result.scalar_one_or_none()
            if not slot:
                raise ValueError("Slot not available or does not exist")

            slot.is_available = False

            appointment = AppointmentModel(
                user_id=user_id,
                slot_id=slot_id,
                status="booked",
            )
            session.add(appointment)
            await session.commit()
            await session.refresh(appointment)

            # Load relationships for response
            result = await session.execute(
                select(AppointmentModel)
                .where(AppointmentModel.id == appointment.id)
                .join(UserModel)
                .join(SlotModel)
            )
            appt = result.scalar_one()
            await session.refresh(appt, ["user", "slot"])

            logger.info(f"Booked appointment: user_id={user_id}, slot_id={slot_id}")
            return Appointment(
                id=appt.id,
                user=User.model_validate(appt.user),
                slot=Slot.model_validate(appt.slot),
                status=appt.status,
                booked_at=appt.booked_at,
            )

    async def get_user_appointments(self, phone: str) -> list[Appointment]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(AppointmentModel)
                .join(UserModel)
                .join(SlotModel)
                .where(
                    and_(
                        UserModel.phone == phone,
                        AppointmentModel.status == "booked",
                    )
                )
                .order_by(SlotModel.date, SlotModel.time)
            )
            rows = result.scalars().all()
            appointments = []
            for appt in rows:
                await session.refresh(appt, ["user", "slot"])
                appointments.append(Appointment(
                    id=appt.id,
                    user=User.model_validate(appt.user),
                    slot=Slot.model_validate(appt.slot),
                    status=appt.status,
                    booked_at=appt.booked_at,
                ))
            return appointments

    async def cancel_appointment(self, appointment_id: int) -> bool:
        async with self._session_factory() as session:
            result = await session.execute(
                select(AppointmentModel).where(AppointmentModel.id == appointment_id)
            )
            appt = result.scalar_one_or_none()
            if not appt:
                return False

            appt.status = "cancelled"
            appt.cancelled_at = datetime.utcnow()

            # Free the slot
            slot_result = await session.execute(
                select(SlotModel).where(SlotModel.id == appt.slot_id)
            )
            slot = slot_result.scalar_one_or_none()
            if slot:
                slot.is_available = True

            await session.commit()
            logger.info(f"Cancelled appointment: id={appointment_id}")
            return True

    async def find_appointment(self, phone: str, date: str, time: str) -> Appointment | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(AppointmentModel)
                .join(UserModel)
                .join(SlotModel)
                .where(
                    and_(
                        UserModel.phone == phone,
                        SlotModel.date == date,
                        SlotModel.time == time,
                        AppointmentModel.status == "booked",
                    )
                )
            )
            appt = result.scalar_one_or_none()
            if not appt:
                return None

            await session.refresh(appt, ["user", "slot"])
            return Appointment(
                id=appt.id,
                user=User.model_validate(appt.user),
                slot=Slot.model_validate(appt.slot),
                status=appt.status,
                booked_at=appt.booked_at,
            )

    # ---- Summary operations ----

    async def save_call_summary(
        self, user_phone: str, summary: str, appointments_json: str, preferences_json: str
    ) -> None:
        async with self._session_factory() as session:
            entry = CallSummaryModel(
                user_phone=user_phone,
                summary=summary,
                appointments_json=appointments_json,
                preferences_json=preferences_json,
            )
            session.add(entry)
            await session.commit()
            logger.info(f"Saved call summary for phone={user_phone}")
