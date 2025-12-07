from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps
from app.core import security
from app.db.session import get_db
from app.db.models import User
from app.schemas import UserCreate, User as UserSchema

router = APIRouter()

@router.post("/open", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user_open(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user without the need to be logged in (Open Registration)
    """
    # 1. Check if user with this email already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system",
        )
    
    # 2. Create new user
    user = User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        is_active=True,
        is_superuser=False,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user
