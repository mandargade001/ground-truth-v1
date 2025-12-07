from fastapi import APIRouter
from app.api.v1.endpoints import login, documents, chat, analytics, health, users

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(health.router, tags=["health"])
from app.api.v1.endpoints import audio
api_router.include_router(audio.router, prefix="/audio", tags=["audio"])
