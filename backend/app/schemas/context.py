from pydantic import BaseModel


class ContextSource(BaseModel):
    source_id: str
    document_id: int
    filename: str
    page_number: int
    chunk_id: int
    text: str


class RetrievedContext(BaseModel):
    query: str
    sources: list[ContextSource]