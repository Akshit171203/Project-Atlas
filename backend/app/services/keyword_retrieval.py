from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.embedding_repository import EmbeddingRepository
from app.schemas.retrieval import RetrievedChunk
from app.services.keyword_search import prepare_keyword_query


class KeywordRetriever:

    def __init__(self):
        self.repository = EmbeddingRepository()

    async def retrieve(
        self,
        session: AsyncSession,
        query: str,
        top_k: int = 20,
        document_id: int | None = None,
    ) -> list[RetrievedChunk]:

        keyword_query = prepare_keyword_query(query)

        if not keyword_query:
            return []

        results = await self.repository.search_keyword(
            session=session,
            query=keyword_query,
            top_k=top_k,
            document_id=document_id,
        )

        retrieved_chunks = []

        for chunk, score in results:

            retrieved_chunks.append(
                RetrievedChunk(
                    document_id=chunk.document_id,
                    filename=chunk.document.filename,
                    chunk_id=chunk.id,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    similarity=float(score),
                )
            )

        return retrieved_chunks