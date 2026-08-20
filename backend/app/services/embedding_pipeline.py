from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.chunk_repository import ChunkRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.services.embedding import embedding_model


class EmbeddingPipeline:

    def __init__(self):
        self.provider = embedding_model
        self.chunk_repository = ChunkRepository()
        self.embedding_repository = EmbeddingRepository()

    async def embed_document(
        self,
        session: AsyncSession,
        document_id: int,
    ) -> int:

        chunks = await self.chunk_repository.get_by_document(
            session=session,
            document_id=document_id,
        )

        if not chunks:
            return 0

        texts = [
            chunk.text
            for chunk in chunks
        ]

        embeddings = self.provider.embed(texts)

        chunk_ids = [
            chunk.id
            for chunk in chunks
        ]

        await self.embedding_repository.create_many(
            session=session,
            chunk_ids=chunk_ids,
            embeddings=embeddings,
        )

        return len(embeddings)