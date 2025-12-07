import asyncio
import asyncpg
import os

async def test_connection():
    configs = [
        ("user", "password", "ragapp"),
        ("postgres", "postgres", "postgres"),
        ("postgres", "password", "postgres"),
        (os.environ.get("USER"), "", "postgres"), # Try local user
    ]
    
    print("Testing connections to localhost:5432...")
    for user, pwd, db in configs:
        try:
            print(f"Trying user='{user}', password='{pwd}', db='{db}'...", end=" ")
            conn = await asyncpg.connect(user=user, password=pwd, database=db, host='localhost', port=5432)
            print("SUCCESS!")
            await conn.close()
            return
        except Exception as e:
            print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
