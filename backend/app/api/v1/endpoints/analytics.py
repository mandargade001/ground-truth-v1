from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.api import deps
from app.db.session import get_db
from app.db.models import Document, ChatSession, ChatMessage

router = APIRouter()

@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(deps.get_current_user)
):
    # Total Documents
    result = await db.execute(select(func.count(Document.id)).where(Document.owner_id == current_user.id))
    total_docs = result.scalar() or 0

    # Total Chats
    result = await db.execute(select(func.count(ChatSession.id)).where(ChatSession.user_id == current_user.id))
    total_sessions = result.scalar() or 0

    # Total Messages
    # Join with Session to filter by user
    # Simplified: just count sessions for MVP or assume session ownership check
    
    # Mock Storage (or calculate real file sizes if stored in DB)
    storage_mb = total_docs * 0.5 # Avg 0.5 MB per doc assumption
    
    return {
        "total_documents": total_docs,
        "total_chats": total_sessions,
        "storage_used_mb": round(storage_mb, 2),
        "system_status": "healthy"
    }
