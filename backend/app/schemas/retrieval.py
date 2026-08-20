from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    document_id: int
    filename: str
    chunk_id: int
    page_number: int
    chunk_index: int
    text: str
    similarity: float
    rerank_score: float | None = None