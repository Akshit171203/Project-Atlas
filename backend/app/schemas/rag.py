from pydantic import BaseModel

from app.schemas.citation import CitationVerificationResult
from app.schemas.evaluation import AnswerRelevanceResult


class RAGResult(BaseModel):
    answer: str
    verification: CitationVerificationResult
    repaired: bool = False
    initial_answer: str | None = None
    initial_verification: CitationVerificationResult | None = None
    answerable: bool
    retrieval_chunk_ids: list[int] = []
    relevance: AnswerRelevanceResult | None = None
