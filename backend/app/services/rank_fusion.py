from collections import defaultdict

from app.schemas.retrieval import RetrievedChunk


class RRFFusion:

    def __init__(self, k: int = 60):
        self.k = k

    def fuse(
        self,
        rankings: list[list[RetrievedChunk]],
        top_k: int = 20,
    ) -> list[RetrievedChunk]:

        scores = defaultdict(float)
        chunks = {}

        for ranking in rankings:

            for rank, chunk in enumerate(
                ranking,
                start=1,
            ):
                scores[chunk.chunk_id] += (
                    1 / (self.k + rank)
                )

                chunks[chunk.chunk_id] = chunk

        ranked_ids = sorted(
            scores,
            key=lambda k: scores[k],
            reverse=True,
        )

        return [
            chunks[chunk_id]
            for chunk_id in ranked_ids[:top_k]
        ]


rrf_fusion = RRFFusion()