import asyncio
from app.db.session import SessionLocal
from sqlalchemy import text

async def main():
    async with SessionLocal() as session:
        result = await session.execute(text("SELECT id, text FROM chunks ORDER BY id LIMIT 50"))
        chunks = result.fetchall()
        for chunk in chunks:
            print(f"--- CHUNK {chunk.id} ---")
            print(chunk.text)
            print("\n")

if __name__ == "__main__":
    asyncio.run(main())
