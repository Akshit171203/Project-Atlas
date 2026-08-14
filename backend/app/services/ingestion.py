from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentRecord
from app.schemas.ingestion import IngestionResult
from app.services.chunking import ChunkingService
from app.services.parser import ParserService
from app.services.storage import StorageService


class IngestionService:

    def __init__(self):
        self.parser = ParserService()
        self.chunker = ChunkingService()
        self.storage = StorageService()

        self.document_repository = DocumentRepository()
        self.chunk_repository = ChunkRepository()

    async def ingest(
        self,
        session: AsyncSession,
        file: UploadFile,
    ) -> IngestionResult:

        file_path = await self.storage.save(file)

        try:
            filename = file.filename or "unknown.pdf"

            document_content = self.parser.parse(
                file_path=file_path,
                filename=filename,
            )

            chunks = self.chunker.chunk(document_content)

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

            return IngestionResult(
                document=DocumentRecord.model_validate(document),
                chunks=chunks,
            )
        except Exception:
            # Clean up the saved file if anything downstream fails
            file_path.unlink(missing_ok=True)
            raise