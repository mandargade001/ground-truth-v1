import asyncio
from app.db.session import AsyncSessionLocal
from app.core.security import get_password_hash
from app.db.models import User
import sys
import os

# Ensure backend dir is in path
sys.path.append(os.getcwd())

async def create_user():
    async with AsyncSessionLocal() as db:
        username = "test@example.com"
        password = "password123"
        hashed_password = get_password_hash(password)
        
        user = User(email=username, hashed_password=hashed_password, is_active=True, is_superuser=False)
        db.add(user)
        try:
            await db.commit()
            print(f"User {username} created successfully.")
        except Exception as e:
            print(f"Error creating user: {e}")
            # Likely already exists

if __name__ == "__main__":
    asyncio.run(create_user())
