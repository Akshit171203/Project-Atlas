from pydantic import BaseModel, Field


class AnswerRelevanceResult(BaseModel):
    relevant: bool
    score: float = Field(ge=0.0, le=1.0)
    reason: str


class RAGEvaluationResult(BaseModel):
    query: str

    expected_answerable: bool
    actual_answerable: bool

    retrieval_hit: bool
    answer_relevant: bool | None = None

    citations_supported: bool | None = None

    repaired: bool = False

    final_success: bool
