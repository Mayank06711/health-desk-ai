import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.config import settings
from app.logger import logger
from app.database.postgres import PostgresDatabase
from app.agent.healthcare_agent import HealthcareAgent

from livekit.agents import (
    AgentServer, AgentSession, JobContext, JobProcess, cli,
)
from livekit.plugins import openai, deepgram, cartesia, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins.simli import AvatarSession, SimliConfig


db: PostgresDatabase | None = None

server = AgentServer()


def prewarm(proc: JobProcess):
    """Pre-load models into RAM at server startup so first request is fast."""
    # Silero VAD — ONNX model loaded once, reused for all sessions
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.05,        # 50ms min speech to trigger
        min_silence_duration=0.4,        # 400ms silence = end of speech (faster than default 550ms)
        prefix_padding_duration=0.3,     # capture 300ms before speech started
        activation_threshold=0.5,        # speech probability threshold
        force_cpu=True,                  # ONNX on CPU, fast enough for VAD
    )
    logger.info("Silero VAD model loaded into RAM")

    # MultilingualModel — transformer model for semantic turn detection
    # loaded once, determines if user is done speaking based on context
    proc.userdata["turn_detector"] = MultilingualModel()
    logger.info("Turn detector model loaded into RAM")


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    global db

    if db is None:
        db = PostgresDatabase(settings.DATABASE_URL)
        await db.initialize()
        logger.info("Database initialized")

    logger.info(f"New session: room={ctx.room.name}")

    # Avatar — only if Simli keys are configured
    avatar = None
    if settings.SIMLI_API_KEY and settings.SIMLI_FACE_ID:
        avatar = AvatarSession(
            simli_config=SimliConfig(
                api_key=settings.SIMLI_API_KEY,
                face_id=settings.SIMLI_FACE_ID,
            ),
        )
        logger.info("Simli avatar enabled")
    else:
        logger.info("Simli not configured, running without avatar")

    session = AgentSession(
        stt=deepgram.STT(
            model="nova-2",
            language="en-US",
            interim_results=True,
            smart_format=True,
            punctuate=True,
        ),
        llm=openai.LLM(
            model=settings.LLM_MODEL,
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
        ),
        tts=cartesia.TTS(
            model="sonic-2",
            voice=settings.CARTESIA_VOICE_ID or "79a125e8-cd45-4c13-8a67-188112f4dd22",
        ),
        vad=ctx.proc.userdata["vad"],
        avatar=avatar,
        turn_handling={
            # Semantic turn detection — uses the pre-loaded transformer model
            # to predict if user is done speaking based on what they said,
            # not just silence. e.g., "I want to book for..." = NOT done
            "turn_detection": ctx.proc.userdata["turn_detector"],

            # Dynamic endpointing — adapts silence threshold based on conversation patterns
            "endpointing": {
                "mode": "dynamic",
                "min_delay": 0.3,    # min 300ms silence before considering turn done
                "max_delay": 2.5,    # max 2.5s silence (absolute cutoff)
                "alpha": 0.85,       # EMA weight for adaptive delay
            },

            # Adaptive interruption — ML-based, distinguishes real interruptions
            # from backchannels like "uh-huh", "right"
            "interruption": {
                "enabled": True,
                "mode": "adaptive",
                "min_duration": 0.5,                 # user must speak 500ms+ to interrupt
                "resume_false_interruption": True,    # resume if it was just "uh-huh"
                "false_interruption_timeout": 2.0,    # wait 2s to confirm false interruption
            },

            # Preemptive generation — start LLM while waiting for turn confirmation
            "preemptive_generation": {
                "enabled": True,
                "preemptive_tts": False,    # only preempt LLM, not TTS (safer)
            },
        },
    )

    @session.on("user_input_transcribed")
    def on_transcript(ev):
        if ev.is_final:
            logger.info(f"User: {ev.transcript}")

    @session.on("agent_state_changed")
    def on_agent_state(ev):
        logger.debug(f"Agent: {ev.old_state} -> {ev.new_state}")

    @session.on("function_tools_executed")
    def on_tools(ev):
        for call, output in ev.zipped():
            logger.info(f"Tool done: {call.name}")

    agent = HealthcareAgent(db=db)
    await session.start(agent=agent, room=ctx.room)


if __name__ == "__main__":
    cli.run_app(server)
