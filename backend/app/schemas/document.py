from datetime import datetime

from pydantic import BaseModel


class Page(BaseModel):
    page_number: int
    text: str

class DocumentContent(BaseModel):
    filename: str
    total_pages: int
    pages: list[Page]

class DocumentRecord(BaseModel):
    """Represents a persisted document (with database ID)."""
    model_config = {"from_attributes": True}

    id: int
    filename: str
    total_pages: int
    created_at: datetime