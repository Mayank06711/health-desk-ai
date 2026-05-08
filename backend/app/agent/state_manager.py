from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from app.logger import logger


class ConversationPhase(Enum):
    GREETING = "greeting"
    IDENTIFYING = "identifying"
    NAME_COLLECTION = "name_collection"
    INTENT_DETECTION = "intent_detection"
    SLOT_SELECTION = "slot_selection"
    BOOKING = "booking"
    VIEWING = "viewing"
    CANCELLING = "cancelling"
    MODIFYING = "modifying"
    CONFIRMING = "confirming"
    WRAPPING_UP = "wrapping_up"
    ENDED = "ended"


@dataclass
class ExtractedData:
    phone: str | None = None
    name: str | None = None
    intent: str | None = None
    selected_date: str | None = None
    selected_time: str | None = None


class ConversationStateManager:

    def __init__(self):
        self._phase = ConversationPhase.GREETING
        self._extracted = ExtractedData()
        self._phase_history: list[tuple[ConversationPhase, str]] = []
        self._tool_calls: list[dict] = []

    @property
    def phase(self) -> ConversationPhase:
        return self._phase

    @property
    def extracted(self) -> ExtractedData:
        return self._extracted

    @property
    def tool_calls(self) -> list[dict]:
        return self._tool_calls

    def transition(self, new_phase: ConversationPhase) -> None:
        """Advisory transition. Logs warning for unexpected jumps but never blocks."""
        old = self._phase
        if old == new_phase:
            return

        self._phase_history.append((old, datetime.now(timezone.utc).isoformat()))
        self._phase = new_phase
        logger.info(f"Phase: {old.value} -> {new_phase.value}")

    def update_extracted(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self._extracted, key) and value is not None:
                setattr(self._extracted, key, value)

        # Auto-transition based on what was extracted
        if kwargs.get("phone") and self._phase == ConversationPhase.GREETING:
            self.transition(ConversationPhase.IDENTIFYING)

    def record_tool_call(self, tool_name: str, result: str) -> None:
        self._tool_calls.append({
            "tool": tool_name,
            "result": result[:500],
            "at": datetime.now(timezone.utc).isoformat(),
        })

    def get_context_injection(self) -> str:
        """Returns context string to append to system prompt."""
        parts = [f"Current phase: {self._phase.value}."]

        if self._extracted.phone:
            parts.append(f"Patient phone: {self._extracted.phone}.")
        if self._extracted.name:
            parts.append(f"Patient name: {self._extracted.name}.")
        if self._extracted.intent:
            parts.append(f"Intent: {self._extracted.intent}.")

        return " ".join(parts)

    def get_summary_data(self) -> dict:
        return {
            "phase_history": [(p.value, ts) for p, ts in self._phase_history],
            "extracted": {
                "phone": self._extracted.phone,
                "name": self._extracted.name,
                "intent": self._extracted.intent,
            },
            "tool_calls": self._tool_calls,
        }
