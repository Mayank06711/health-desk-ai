import json
from livekit.agents import Agent, RunContext
from livekit.agents.llm import function_tool

from app.agent.state_manager import ConversationStateManager, ConversationPhase
from app.agent.context_manager import ContextManager
from app.agent.prompts import get_system_prompt
from app.services.appointment_service import AppointmentService
from app.services.summary_service import SummaryService
from app.database.base import DatabaseBase
from app.config import settings
from app.logger import logger


class HealthcareAgent(Agent):

    def __init__(self, db: DatabaseBase):
        self._db = db
        self._appointment_service = AppointmentService(db)
        self._summary_service = SummaryService(api_key=settings.OPENAI_API_KEY)
        self._state = ConversationStateManager()
        self._context = ContextManager(openai_api_key=settings.OPENAI_API_KEY)

        super().__init__(instructions=get_system_prompt())

    async def on_enter(self) -> None:
        logger.info("Agent entered, greeting user")
        self.session.generate_reply(
            instructions="Greet the patient warmly and ask how you can help today. Keep it short."
        )

    async def _publish_tool_status(self, tool: str, status: str, data: dict | None = None) -> None:
        payload = json.dumps({"tool": tool, "status": status, "data": data or {}})
        try:
            await self.session.room.local_participant.publish_data(
                payload.encode(), topic="tool-status"
            )
        except Exception as e:
            logger.error(f"Failed to publish tool status: {e}")

    @function_tool()
    async def identify_user(self, context: RunContext, phone: str) -> str:
        """Identify a patient by their phone number. Call this when the patient provides their phone number.
        Args:
            phone: The patient's phone number, digits only (e.g. "9876543210")
        """
        logger.info(f"Tool: identify_user(phone={phone})")
        await self._publish_tool_status("identify_user", "in_progress")

        try:
            self._state.update_extracted(phone=phone)
            self._context.set_critical_fact("phone", phone)

            result = await self._appointment_service.identify_user(phone)

            if result["user"] and result["user"].name:
                self._state.update_extracted(name=result["user"].name)
                self._context.set_critical_fact("name", result["user"].name)
                self._state.transition(ConversationPhase.INTENT_DETECTION)
            else:
                self._state.transition(ConversationPhase.NAME_COLLECTION)

            await self._publish_tool_status("identify_user", "completed", {
                "found": result["found"],
                "appointment_count": result["appointment_count"],
            })
            self._state.record_tool_call("identify_user", str(result["found"]))

            return json.dumps({
                "found": result["found"],
                "name": result["user"].name if result["user"] else None,
                "appointment_count": result["appointment_count"],
            })
        except Exception as e:
            logger.error(f"identify_user failed: {e}")
            await self._publish_tool_status("identify_user", "completed", {"error": True})
            return json.dumps({"error": "Sorry, I had trouble looking up that phone number. Could you try again?"})

    @function_tool()
    async def fetch_slots(self, context: RunContext) -> str:
        """Fetch available appointment slots. Call this when the patient asks about availability or wants to book.
        """
        logger.info("Tool: fetch_slots()")
        await self._publish_tool_status("fetch_slots", "in_progress")

        try:
            self._state.transition(ConversationPhase.SLOT_SELECTION)
            slots = await self._appointment_service.get_available_slots()

            result = [{"date": s.date, "time": s.time} for s in slots[:10]]
            total = len(slots)

            await self._publish_tool_status("fetch_slots", "completed", {"count": total})
            self._state.record_tool_call("fetch_slots", f"{total} slots available")

            return json.dumps({"slots": result, "total_available": total})
        except Exception as e:
            logger.error(f"fetch_slots failed: {e}")
            await self._publish_tool_status("fetch_slots", "completed", {"error": True})
            return json.dumps({"error": "Sorry, I could not fetch available slots right now. Please try again."})

    @function_tool()
    async def book_appointment(
        self, context: RunContext, name: str, phone: str, date: str, time: str
    ) -> str:
        """Book an appointment for the patient. Only call after the patient has confirmed the date and time.
        Args:
            name: Patient's full name
            phone: Patient's phone number
            date: Appointment date in YYYY-MM-DD format (e.g. "2026-05-12")
            time: Appointment time in HH:MM 24-hour format (e.g. "14:00")
        """
        logger.info(f"Tool: book_appointment({name}, {phone}, {date}, {time})")
        await self._publish_tool_status("book_appointment", "in_progress", {
            "name": name, "date": date, "time": time,
        })

        try:
            self._state.transition(ConversationPhase.BOOKING)
            self._context.set_critical_fact("name", name)

            result = await self._appointment_service.book_appointment(phone, date, time, name)

            await self._publish_tool_status("book_appointment", "completed", {
                "success": result["success"], "message": result["message"],
            })
            self._state.record_tool_call("book_appointment", result["message"])

            if result["success"]:
                self._state.transition(ConversationPhase.CONFIRMING)

            return json.dumps({"success": result["success"], "message": result["message"]})
        except Exception as e:
            logger.error(f"book_appointment failed: {e}")
            await self._publish_tool_status("book_appointment", "completed", {"error": True})
            return json.dumps({"error": "Sorry, I had trouble booking that appointment. Please try again."})

    @function_tool()
    async def retrieve_appointments(self, context: RunContext, phone: str) -> str:
        """Retrieve all upcoming appointments for a patient.
        Args:
            phone: Patient's phone number
        """
        logger.info(f"Tool: retrieve_appointments({phone})")
        await self._publish_tool_status("retrieve_appointments", "in_progress")

        try:
            self._state.transition(ConversationPhase.VIEWING)
            appointments = await self._appointment_service.get_user_appointments(phone)

            result = [
                {"date": a.slot.date, "time": a.slot.time, "status": a.status, "id": a.id}
                for a in appointments
            ]

            await self._publish_tool_status("retrieve_appointments", "completed", {
                "count": len(result),
            })
            self._state.record_tool_call("retrieve_appointments", f"{len(result)} found")

            if not result:
                return "No upcoming appointments found for this phone number."
            return json.dumps(result)
        except Exception as e:
            logger.error(f"retrieve_appointments failed: {e}")
            await self._publish_tool_status("retrieve_appointments", "completed", {"error": True})
            return json.dumps({"error": "Sorry, I could not retrieve appointments right now."})

    @function_tool()
    async def cancel_appointment(self, context: RunContext, phone: str, date: str, time: str) -> str:
        """Cancel an existing appointment. Only call after the patient confirms they want to cancel.
        Args:
            phone: Patient's phone number
            date: Appointment date to cancel (YYYY-MM-DD)
            time: Appointment time to cancel (HH:MM)
        """
        logger.info(f"Tool: cancel_appointment({phone}, {date}, {time})")
        await self._publish_tool_status("cancel_appointment", "in_progress", {
            "date": date, "time": time,
        })

        try:
            self._state.transition(ConversationPhase.CANCELLING)
            result = await self._appointment_service.cancel_appointment(phone, date, time)

            await self._publish_tool_status("cancel_appointment", "completed", result)
            self._state.record_tool_call("cancel_appointment", result["message"])

            if result["success"]:
                self._state.transition(ConversationPhase.CONFIRMING)

            return json.dumps(result)
        except Exception as e:
            logger.error(f"cancel_appointment failed: {e}")
            await self._publish_tool_status("cancel_appointment", "completed", {"error": True})
            return json.dumps({"error": "Sorry, I had trouble cancelling that appointment. Please try again."})

    @function_tool()
    async def modify_appointment(
        self, context: RunContext, phone: str,
        old_date: str, old_time: str, new_date: str, new_time: str
    ) -> str:
        """Modify an existing appointment to a new date and time. Only call after patient confirms both old and new slots.
        Args:
            phone: Patient's phone number
            old_date: Current appointment date (YYYY-MM-DD)
            old_time: Current appointment time (HH:MM)
            new_date: New desired date (YYYY-MM-DD)
            new_time: New desired time (HH:MM)
        """
        logger.info(f"Tool: modify_appointment({phone}, {old_date} {old_time} -> {new_date} {new_time})")
        await self._publish_tool_status("modify_appointment", "in_progress", {
            "old": {"date": old_date, "time": old_time},
            "new": {"date": new_date, "time": new_time},
        })

        try:
            self._state.transition(ConversationPhase.MODIFYING)
            result = await self._appointment_service.modify_appointment(
                phone, old_date, old_time, new_date, new_time
            )

            await self._publish_tool_status("modify_appointment", "completed", {
                "success": result["success"], "message": result["message"],
            })
            self._state.record_tool_call("modify_appointment", result["message"])

            if result["success"]:
                self._state.transition(ConversationPhase.CONFIRMING)

            return json.dumps({"success": result["success"], "message": result["message"]})
        except Exception as e:
            logger.error(f"modify_appointment failed: {e}")
            await self._publish_tool_status("modify_appointment", "completed", {"error": True})
            return json.dumps({"error": "Sorry, I had trouble modifying that appointment. Please try again."})

    @function_tool()
    async def end_conversation(self, context: RunContext) -> str:
        """End the conversation and generate a summary. Call when the patient says goodbye or is done.
        """
        logger.info("Tool: end_conversation()")
        await self._publish_tool_status("end_conversation", "in_progress")

        try:
            self._state.transition(ConversationPhase.ENDED)

            phone = self._state.extracted.phone
            chat_history = self._context.get_full_history()
            appointments = []
            if phone:
                appts = await self._appointment_service.get_user_appointments(phone)
                appointments = [
                    {"date": a.slot.date, "time": a.slot.time, "status": a.status}
                    for a in appts
                ]

            summary = await self._summary_service.generate_summary(
                chat_history=chat_history,
                user_phone=phone,
                appointments=appointments,
            )

            if phone:
                await self._db.save_call_summary(
                    user_phone=phone,
                    summary=summary.get("summary", ""),
                    appointments_json=json.dumps(summary.get("appointments", [])),
                    preferences_json=json.dumps(summary.get("preferences", [])),
                )

            try:
                await self.session.room.local_participant.publish_data(
                    json.dumps(summary).encode(), topic="call-summary"
                )
            except Exception as e:
                logger.error(f"Failed to publish call summary: {e}")

            await self._publish_tool_status("end_conversation", "completed")
            return json.dumps(summary)
        except Exception as e:
            logger.error(f"end_conversation failed: {e}")
            await self._publish_tool_status("end_conversation", "completed", {"error": True})
            return json.dumps({"summary": "Call ended. Summary could not be generated.", "appointments": [], "preferences": [], "timestamp": ""})
