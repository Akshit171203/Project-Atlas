from sentence_transformers import CrossEncoder

from app.core.config import settings
from app.schemas.retrieval import RetrievedChunk


class Reranker:

    def __init__(self):
        self.model = CrossEncoder(
            settings.RERANKER_MODEL
        )

    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:

        if not chunks:
            return []

        pairs = [
            (query, chunk.text)
            for chunk in chunks
        ]

        scores = self.model.predict(pairs)  # type: ignore

        scored_chunks = []

        for chunk, score in zip(chunks, scores):
            chunk.rerank_score = float(score)
            scored_chunks.append(chunk)

        scored_chunks.sort(
            key=lambda chunk: chunk.rerank_score, # type: ignore
            reverse=True,
        )

        return scored_chunks[:top_k]

# Shared model instance
reranker_model = Reranker()