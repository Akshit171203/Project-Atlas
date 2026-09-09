from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.retrieval import RetrievedChunk
from app.services.reranker import reranker_model
from app.services.retrieval import Retriever


class RerankedRetriever:

    def __init__(self):
        self.retriever = Retriever()
        self.reranker = reranker_model

    async def retrieve(
        self,
        session: AsyncSession,
        query: str,
        candidate_k: int = 10,
        top_k: int = 5,
        document_id: int | None = None,
    ) -> list[RetrievedChunk]:

        candidates = await self.retriever.retrieve(
            session=session,
            query=query,
            top_k=candidate_k,
            document_id=document_id,
        )

        return self.reranker.rerank(
            query=query,
            chunks=candidates,
            top_k=top_k,
        )
