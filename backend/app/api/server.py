from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from livekit import api as livekit_api

from app.config import settings
from app.logger import logger

app = FastAPI(title="Health Desk AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TokenRequest(BaseModel):
    identity: str
    room: str = "health-desk"
    name: str = "Patient"


class TokenResponse(BaseModel):
    token: str
    url: str


@app.post("/api/token", response_model=TokenResponse)
async def create_token(req: TokenRequest) -> TokenResponse:
    token = (
        livekit_api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(req.identity)
        .with_name(req.name)
        .with_grants(livekit_api.VideoGrants(room_join=True, room=req.room))
        .to_jwt()
    )
    logger.info(f"Token generated: identity={req.identity}, room={req.room}")
    return TokenResponse(token=token, url=settings.LIVEKIT_URL)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "health-desk-ai"}
