from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.services.chunking import ChunkingService
from app.services.pdf_parser import PDFParser


class IngestionService:

    def __init__(self):
        self.parser = PDFParser()
        self.chunker = ChunkingService()

        self.document_repository = DocumentRepository()
        self.chunk_repository = ChunkRepository()

    async def ingest(
        self,
        session: AsyncSession,
        file: UploadFile,
    ):

        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)

        filename = file.filename or "unknown.pdf"
        file_path = upload_dir / filename

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        document_content = self.parser.parse(
            pdf_path=str(file_path),
            filename=filename,
        )

        chunks = self.chunker.chunk_document(document_content)

        document = await self.document_repository.create(
            session=session,
            filename=document_content.filename,
            total_pages=document_content.total_pages,
        )

        await self.chunk_repository.create_many(
            session=session,
            document_id=document.id,
            chunks=chunks,
        )

        await session.commit()

        return document, chunks