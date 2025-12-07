from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from app.core.config import settings
from app.core.logging import logger
import redis.asyncio as redis

router = APIRouter()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Perform a deep health check of dependencies.
    """
    health_status = {
        "status": "ok",
        "database": "unknown",
        "redis": "unknown"
    }

    # Check Database
    try:
        await db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = "disconnected"
        health_status["status"] = "error"
        logger.error("health_check_db_failed", error=str(e))

    # Check Redis
    try:
        r = redis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}", encoding="utf-8", decode_responses=True)
        await r.ping()
        await r.close()
        health_status["redis"] = "connected"
    except Exception as e:
        health_status["redis"] = "disconnected"
        health_status["status"] = "error"
        logger.error("health_check_redis_failed", error=str(e))

    if health_status["status"] == "error":
        raise HTTPException(status_code=503, detail=health_status)

    return health_status
