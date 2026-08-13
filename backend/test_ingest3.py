import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
from app.services.ingestion import IngestionService
from app.db.session import SessionLocal
import sys

class MockUploadFile:
    def __init__(self, filename, path):
        self.filename = filename
        self.path = path
    
    async def read(self):
        with open(self.path, "rb") as f:
            return f.read()

async def main():
    service = IngestionService()
    file = MockUploadFile("valid.pdf", "valid.pdf")
    
    async with SessionLocal() as session:
        try:
            document, chunks = await service.ingest(session, file)
            print("Success!", document.id, len(chunks))
        except Exception as e:
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
