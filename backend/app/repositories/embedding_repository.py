from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.embedding import Embedding


class EmbeddingRepository:

    async def create_many(
        self,
        session: AsyncSession,
        chunk_ids: list[int],
        embeddings: list[list[float]],
    ) -> None:

        records = [
            Embedding(
                chunk_id=chunk_id,
                model=settings.EMBEDDING_MODEL,
                dimensions=settings.EMBEDDING_DIMENSIONS,
                vector=vector,
            )
            for chunk_id, vector in zip(chunk_ids, embeddings)
        ]

        session.add_all(records)

        await session.flush()