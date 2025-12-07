from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps
from app.db.session import get_db, AsyncSessionLocal
from app.db.models import User, ChatSession, ChatMessage
from app.rag.retrieval import chat_stream

router = APIRouter()

class ChatRequest(BaseModel):
    session_id: Optional[int] = None
    message: str

class ChatResponse(BaseModel):
    session_id: int
    message: str

async def save_bot_message_background(session_id: int, message_content: str):
    async with AsyncSessionLocal() as db:
        msg = ChatMessage(role="assistant", content=message_content, session_id=session_id)
        db.add(msg)
        await db.commit()

@router.post("/message")
async def chat_message(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # 1. Get or Create Session
    if request.session_id:
        result = await db.execute(select(ChatSession).where(ChatSession.id == request.session_id, ChatSession.user_id == current_user.id))
        session = result.scalars().first()
        if not session:
             raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = ChatSession(user_id=current_user.id)
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
    # 2. Get History (Last 10 messages)
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
    )
    messages = result.scalars().all()
    history = [(m.content, "") if m.role == "user" else ("", m.content) for m in reversed(messages)]
    
    # 3. Save User Message
    user_msg = ChatMessage(role="user", content=request.message, session_id=session.id)
    db.add(user_msg)
    await db.commit()

    # 4. Stream Response & Accumulate for Persistence
    async def generate():
        full_response = ""
        async for token in chat_stream(request.message, history):
            # Check if token contains the JSON metadata line
            # This is a bit brittle if the JSON is split across tokens, 
            # but given our generator yields the full JSON line first, it should be safe.
            if token.startswith('{"type": "sources"'):
                 # It's the metadata chunk, yield it but don't save to DB text
                 yield token
                 continue
            
            full_response += token
            yield token
        
        await save_bot_message_background(session.id, full_response)

    return StreamingResponse(generate(), media_type="text/event-stream")

@router.get("/sessions", response_model=List[ChatResponse])
async def get_chat_sessions(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Retrieve chat sessions for the current user.
    """
    # Create a result model that fits the response
    # We might need a better response model for sessions listing
    # For now reusing ChatResponse or creating a new one
    
    # Fetch sessions with pagination
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    sessions = result.scalars().all()
    
    response_data = []
    for s in sessions:
        # Fetch first user message for title
        # Optimized: query only the first message content
        msg_result = await db.execute(
            select(ChatMessage.content)
            .where(ChatMessage.session_id == s.id, ChatMessage.role == "user")
            .order_by(ChatMessage.created_at.asc())
            .limit(1)
        )
        first_msg = msg_result.scalar_one_or_none()
        
        # Truncate title
        title = first_msg[:50] + "..." if first_msg and len(first_msg) > 50 else (first_msg or f"Conversation {s.id}")
        
        response_data.append({
            "session_id": s.id,
            "message": title
        })
    
    return response_data
