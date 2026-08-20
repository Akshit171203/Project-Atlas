from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.embedding_repository import EmbeddingRepository
from app.schemas.retrieval import RetrievedChunk
from app.services.embedding import embedding_model


class Retriever:

    def __init__(self):
        self.embedding_provider = embedding_model
        self.embedding_repository = EmbeddingRepository()

    async def retrieve(
        self,
        session: AsyncSession,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:

        query_vector = self.embedding_provider.embed(
            [query]
        )[0]

        results = await self.embedding_repository.search_similar(
            session=session,
            query_vector=query_vector,
            top_k=top_k,
        )

        retrieved_chunks = []

        for chunk, distance in results:

            similarity = 1 - distance

            retrieved_chunks.append(
                RetrievedChunk(
                    document_id=chunk.document_id,
                    filename=chunk.document.filename,
                    chunk_id=chunk.id,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    similarity=similarity,
                )
            )

        return retrieved_chunks