from pydantic import BaseModel

from app.schemas.chunk import Chunk
from app.schemas.document import DocumentRecord

class IngestionResult(BaseModel):
    document: DocumentRecord
    chunks: list[Chunk]
