from pydantic import BaseModel


class Chunk(BaseModel):
    page_number: int
    chunk_index: int
    text: str