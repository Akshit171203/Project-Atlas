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
        query_variants: list[str] | None = None,
    ) -> list[RetrievedChunk]:

        # Each phrasing gets its own vector-search pass (cheap, local —
        # not an LLM call), so a chunk that only the original phrasing's
        # embedding would surface, or only a variant's would, both get a
        # chance to enter the candidate pool.
        #
        # Tried also merging in keyword-search candidates here, reasoning
        # that vector search can miss a chunk entirely (confirmed: chunk
        # 375 never appeared in vector search's top 10 for a real query,
        # while keyword search found it via exact term overlap on
        # "library"). Reverted — it caused a real regression: for
        # "summarise chapter 1 for me", keyword search matched a chunk
        # that is literally just a page header ("Chapter One: Lesson 1")
        # on lexical overlap alone, the reranker (already known to be
        # lexically sensitive — see EVIDENCE_GATE_CALIBRATION.md) scored
        # it +0.5, and a query that correctly refused before started
        # generating an answer it shouldn't have. It also didn't even fix
        # the case it was built for — chunk 375/380 still failed on
        # absolute rerank score once in the pool, since reranking is
        # retrieval-source-agnostic and the bottleneck was never pool
        # composition. Net negative on the eval suite (8/11 -> 7/11), so
        # not worth the complexity. See EVIDENCE_GATE_CALIBRATION.md.
        queries = [query] + [q for q in (query_variants or []) if q != query]

        by_id: dict[int, RetrievedChunk] = {}
        for q in queries:
            candidates = await self.retriever.retrieve(
                session=session,
                query=q,
                top_k=candidate_k,
                document_id=document_id,
            )
            for chunk in candidates:
                by_id.setdefault(chunk.chunk_id, chunk)

        merged = list(by_id.values())

        if len(queries) == 1:
            return self.reranker.rerank(
                query=query,
                chunks=merged,
                top_k=top_k,
            )

        # Score every candidate against every phrasing and keep each
        # chunk's best score — the reranker is sensitive enough to exact
        # wording that a genuinely relevant chunk can score well under one
        # phrasing and poorly under another (see
        # EVIDENCE_GATE_CALIBRATION.md). A chunk should survive if it
        # matches *any* phrasing of the same question.
        best_score: dict[int, float] = {}
        for q in queries:
            scored = self.reranker.rerank(
                query=q,
                chunks=merged,
                top_k=len(merged),
            )
            for chunk in scored:
                current = best_score.get(chunk.chunk_id)
                if current is None or chunk.rerank_score > current:
                    best_score[chunk.chunk_id] = chunk.rerank_score

        for chunk in merged:
            chunk.rerank_score = best_score[chunk.chunk_id]

        merged.sort(key=lambda c: c.rerank_score, reverse=True)  # type: ignore[arg-type,return-value]

        return merged[:top_k]
