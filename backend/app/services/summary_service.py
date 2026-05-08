import json
from datetime import datetime, timezone
from openai import AsyncOpenAI
from app.logger import logger

SUMMARY_PROMPT = """Analyze this voice conversation between a healthcare AI assistant and a patient.
Generate a structured JSON summary.

The conversation transcript:
{transcript}

Current appointments for this patient:
{appointments}

Return a JSON object with these exact fields:
- summary: 2-3 sentence overview of what happened in the call
- appointments: list of appointments discussed (each with date, time, status)
- preferences: list of any patient preferences mentioned (time preference, doctor preference, etc.)
- intent: primary intent of the call (book/cancel/modify/inquire)
- timestamp: current ISO timestamp
"""


class SummaryService:

    def __init__(self, api_key: str):
        self._client = AsyncOpenAI(api_key=api_key)

    async def generate_summary(
        self,
        chat_history: list[dict],
        user_phone: str | None,
        appointments: list[dict],
    ) -> dict:
        """Generate structured call summary. Must complete within 10 seconds."""

        transcript = "\n".join(
            f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
            for msg in chat_history
            if msg.get("content")
        )

        if not transcript.strip():
            return {
                "summary": "The call ended without any conversation.",
                "appointments": appointments,
                "preferences": [],
                "intent": "unknown",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        prompt = SUMMARY_PROMPT.format(
            transcript=transcript,
            appointments=json.dumps(appointments) if appointments else "None",
        )

        try:
            response = await self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                timeout=10.0,
            )
            result = json.loads(response.choices[0].message.content)
            result.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
            logger.info("Call summary generated successfully")
            return result

        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return {
                "summary": "Call summary could not be generated.",
                "appointments": appointments,
                "preferences": [],
                "intent": "unknown",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
