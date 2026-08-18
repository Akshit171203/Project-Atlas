from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.chunk import Chunk
from app.schemas.chunk import Chunk as ChunkSchema


class ChunkRepository:

    async def create_many(
        self,
        session: AsyncSession,
        document_id: int,
        chunks: list[ChunkSchema],
    ) -> None:

        db_chunks = [
            Chunk(
                document_id=document_id,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
            )
            for chunk in chunks
        ]

        session.add_all(db_chunks)

        await session.flush()

    async def get_by_document(
        self,
        session: AsyncSession,
        document_id: int,
    ):
        result = await session.execute(
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .order_by(Chunk.chunk_index)
        )

        return list(result.scalars().all())