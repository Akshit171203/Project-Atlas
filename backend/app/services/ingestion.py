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
from app.services.embedding_pipeline import EmbeddingPipeline


class IngestionService:

    def __init__(self):
        self.parser = ParserService()
        self.chunker = ChunkingService()
        self.storage = StorageService()

        self.document_repository = DocumentRepository()
        self.chunk_repository = ChunkRepository()
        self.embedding_pipeline = EmbeddingPipeline()

    async def ingest(
        self,
        session: AsyncSession,
        file: UploadFile,
    ):

        stored_file = await self.storage.save(file)

        try:
            document_content = self.parser.parse(
                stored_file=stored_file,
            )

            chunks = self.chunker.chunk(document_content)

            document = await self.document_repository.save(
                session=session,
                filename=document_content.filename,
                total_pages=document_content.total_pages,
            )

            await self.chunk_repository.create_many(
                session=session,
                document_id=document.id,
                chunks=chunks,
            )

            embedding_count = await self.embedding_pipeline.embed_document(
                session=session,
                document_id=document.id,
            )

            await session.commit()

            return document, chunks, embedding_count
        except Exception:
            # Clean up the saved file if anything downstream fails
            stored_file.path.unlink(missing_ok=True)
            raise