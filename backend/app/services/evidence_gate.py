from app.schemas.retrieval import RetrievedChunk


class EvidenceGate:

    def __init__(
        self,
        # cross-encoder/ms-marco-MiniLM-L6-v2 scores aren't centered at 0:
        # measured genuinely relevant matches at -0.33 to 1.4, vague/no-match
        # queries at -3.4 to -9.5, and true off-topic queries at -10.6 to
        # -11.3. 0.0 was rejecting real, answerable questions (e.g. a
        # specific question about book content scored -0.33 and was wrongly
        # refused). -2.0 sits in the gap between "relevant" and "no match"
        # — see backend/EVIDENCE_GATE_CALIBRATION.md.
        min_rerank_score: float = -2.0,
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