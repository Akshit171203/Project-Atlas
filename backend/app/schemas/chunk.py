from pydantic import BaseModel


class Chunk(BaseModel):
    id: str
    page_number: int
    chunk_index: int
    text: str