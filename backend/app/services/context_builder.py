from app.schemas.context import (
    ContextSource,
    RetrievedContext,
)
from app.schemas.retrieval import RetrievedChunk


class ContextBuilder:

    def build(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> RetrievedContext:

        sources = []

        for index, chunk in enumerate(
            chunks,
            start=1,
        ):
            sources.append(
                ContextSource(
                    source_id=f"S{index}",
                    document_id=chunk.document_id,
                    filename=chunk.filename,
                    page_number=chunk.page_number,
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                )
            )

        return RetrievedContext(
            query=query,
            sources=sources,
        )