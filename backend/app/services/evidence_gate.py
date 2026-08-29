from app.schemas.retrieval import RetrievedChunk


class EvidenceGate:

    def __init__(
        self,
        min_rerank_score: float = 0.0,
    ):
        self.min_rerank_score = min_rerank_score

    def is_answerable(
        self,
        chunks: list[RetrievedChunk],
    ) -> bool:

        scores = [
            chunk.rerank_score
            for chunk in chunks
            if chunk.rerank_score is not None
        ]

        if not scores:
            return False

        return max(scores) >= self.min_rerank_score