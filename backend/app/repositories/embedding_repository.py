from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models import Chunk, Embedding
from app.services.keyword_search import prepare_keyword_query


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

    async def search_similar(
        self,
        session: AsyncSession,
        query_vector: list[float],
        top_k: int = 5,
        document_id: int | None = None,
    ):
        distance = Embedding.vector.cosine_distance(
            query_vector
        )

        stmt = (
            select(
                Chunk,
                distance.label("distance"),
            )
            .options(selectinload(Chunk.document))
            .join(
                Embedding,
                Embedding.chunk_id == Chunk.id,
            )
            .where(
                Embedding.model == settings.EMBEDDING_MODEL
            )
        )

        if document_id is not None:
            stmt = stmt.where(
                Chunk.document_id == document_id
            )

        result = await session.execute(
            stmt.order_by(distance)
            .limit(top_k)
        )

        return result.all()

    async def search_keyword(
        self,
        session: AsyncSession,
        query: str,
        top_k: int = 20,
        document_id: int | None = None,
    ):
        prepared_query = prepare_keyword_query(query)
        search_query = func.websearch_to_tsquery(
            "english",
            prepared_query,
        )

        text_vector = func.to_tsvector(
            "english",
            Chunk.text,
        )

        rank = func.ts_rank_cd(
            text_vector,
            search_query,
        )

        stmt = (
            select(
                Chunk,
                rank.label("score"),
            )
            .options(selectinload(Chunk.document))
            .where(
                text_vector.op("@@")(search_query)
            )
        )

        if document_id is not None:
            stmt = stmt.where(
                Chunk.document_id == document_id
            )

        result = await session.execute(
            stmt.order_by(rank.desc())
            .limit(top_k)
        )

        return result.all()