from pydantic import BaseModel

from app.schemas.citation import CitationVerificationResult


class RAGResult(BaseModel):
    answer: str
    verification: CitationVerificationResult
    repaired: bool = False
    initial_answer: str | None = None
    initial_verification: CitationVerificationResult | None = None
