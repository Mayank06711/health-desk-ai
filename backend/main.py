import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

# LOCAL_MODELS_ONLY controls whether HuggingFace downloads models or uses cached ones
# - true: uses pre-downloaded models only (for us, we already have them)
# - false (default): downloads models on first run (for new users cloning the repo)
# Pass via CLI: LOCAL_MODELS_ONLY=true python main.py start
# Pass via docker-compose: environment: LOCAL_MODELS_ONLY=true
if os.environ.get("LOCAL_MODELS_ONLY", "false").lower() == "true":
    os.environ["HF_HUB_OFFLINE"] = "1"

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
    """Pre-load heavy models into RAM at server startup."""
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.05,
        min_silence_duration=0.4,
        prefix_padding_duration=0.3,
        activation_threshold=0.5,
        force_cpu=True,
    )
    logger.info("Silero VAD model loaded into RAM")


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    global db

    if db is None:
        db = PostgresDatabase(settings.DATABASE_URL)
        await db.initialize()
        logger.info("Database initialized")

    # Connect to the room first — required before anything else
    await ctx.connect()
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
        # Auto-close if user is away (no speech) for 15 seconds
        user_away_timeout=15,
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
        turn_handling={
            # MultilingualModel must be created here (not in prewarm) because
            # its __init__ calls get_job_context().inference_executor which
            # only exists inside a job entrypoint
            "turn_detection": MultilingualModel(),

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

    async def publish_data(topic: str, data: dict) -> None:
        try:
            await ctx.room.local_participant.publish_data(
                json.dumps(data).encode(), topic=topic
            )
        except Exception as e:
            logger.error(f"Failed to publish {topic}: {e}")

    @session.on("user_input_transcribed")
    def on_transcript(ev):
        if ev.is_final:
            logger.info(f"User: {ev.transcript}")
            agent._context.add_message("user", ev.transcript)
            import asyncio
            asyncio.ensure_future(publish_data("transcript", {"role": "user", "text": ev.transcript}))

    @session.on("conversation_item_added")
    def on_conversation_item(ev):
        try:
            msg = ev.item
            logger.info(f"Conv item: role={msg.role}, type={msg.type}")
            if msg.role == "assistant":
                text = msg.text_content if hasattr(msg, 'text_content') else ""
                if not text and hasattr(msg, 'content'):
                    if isinstance(msg.content, str):
                        text = msg.content
                    elif isinstance(msg.content, list):
                        text = " ".join(
                            c.text if hasattr(c, 'text') else str(c)
                            for c in msg.content
                        )
                if text:
                    logger.info(f"Agent: {text[:200]}")
                    agent._context.add_message("assistant", text)
                    import asyncio
                    asyncio.ensure_future(publish_data("transcript", {"role": "agent", "text": text}))
        except Exception as e:
            logger.error(f"conversation_item handler error: {e}")

    @session.on("agent_state_changed")
    def on_agent_state(ev):
        logger.debug(f"Agent: {ev.old_state} -> {ev.new_state}")

    @session.on("function_tools_executed")
    def on_tools(ev):
        for call, output in ev.zipped():
            logger.info(f"Tool done: {call.name}")

    agent = HealthcareAgent(db=db)

    # Start avatar BEFORE agent session so it can capture audio output from the start
    if avatar:
        await avatar.start(
            agent_session=session,
            room=ctx.room,
            livekit_url=settings.LIVEKIT_URL,
            livekit_api_key=settings.LIVEKIT_API_KEY,
            livekit_api_secret=settings.LIVEKIT_API_SECRET,
        )
        logger.info("Simli avatar session started")

    await session.start(agent=agent, room=ctx.room)


if __name__ == "__main__":
    cli.run_app(server)
