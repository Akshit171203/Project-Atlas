from pydantic import BaseModel
    

class Page(BaseModel):
    page_number: int
    text: str

class DocumentContent(BaseModel):
    filename: str
    total_pages: int
    pages: list[Page]