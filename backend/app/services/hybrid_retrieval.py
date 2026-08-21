from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.retrieval import RetrievedChunk
from app.services.keyword_retrieval import KeywordRetriever
from app.services.rank_fusion import rrf_fusion
from app.services.reranker import reranker_model
from app.services.retrieval import Retriever


class HybridRetriever:

    def __init__(self):
        self.vector_retriever = Retriever()
        self.keyword_retriever = KeywordRetriever()
        self.reranker = reranker_model

    async def retrieve(
        self,
        session: AsyncSession,
        query: str,
        candidate_k: int = 20,
        top_k: int = 5,
        document_id: int | None = None,
    ) -> list[RetrievedChunk]:

        vector_results = await self.vector_retriever.retrieve(
            session=session,
            query=query,
            top_k=candidate_k,
            document_id=document_id,
        )

        keyword_results = await self.keyword_retriever.retrieve(
            session=session,
            query=query,
            top_k=candidate_k,
            document_id=document_id,
        )

        fused_results = rrf_fusion.fuse(
            rankings=[
                vector_results,
                keyword_results,
            ],
            top_k=candidate_k,
        )

        return self.reranker.rerank(
            query=query,
            chunks=fused_results,
            top_k=top_k,
        )