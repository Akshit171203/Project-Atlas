from app.schemas.retrieval import RetrievedChunk


class SourceRegistry:

    def __init__(
        self,
        chunks: list[RetrievedChunk],
    ):
        self.sources = {
            f"S{index}": chunk
            for index, chunk in enumerate(chunks, start=1)
        }

    def get(
        self,
        source_id: str,
    ) -> RetrievedChunk | None:

        return self.sources.get(source_id)

    def all(self) -> dict[str, RetrievedChunk]:
        return self.sources