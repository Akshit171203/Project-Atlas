from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.evaluation import RAGEvaluationResult
from app.services.rag import RAGService


rag_service = RAGService()


async def evaluate_case(
    session: AsyncSession,
    case: dict,
) -> RAGEvaluationResult:

    result = await rag_service.answer(
        session=session,
        query=case["query"],
        document_id=case.get("document_id"),
    )

    expected_answerable = case["answerable"]
    actual_answerable = result.answerable

    retrieval_hit = bool(
        result.retrieval_chunk_ids
    )

    answer_relevant = None

    if result.relevance is not None:
        answer_relevant = result.relevance.relevant

    citations_supported = None

    if result.answerable:
        citations_supported = (
            result.verification.all_supported
        )

    # Determine whether the complete RAG request
    # succeeded according to the expected behavior.
    if expected_answerable != actual_answerable:

        final_success = False

    elif not expected_answerable:

        # Correct abstention is a successful result.
        final_success = True

    else:

        final_success = (
            citations_supported is True
            and answer_relevant is True
        )

    return RAGEvaluationResult(
        query=case["query"],
        expected_answerable=expected_answerable,
        actual_answerable=actual_answerable,
        retrieval_hit=retrieval_hit,
        answer_relevant=answer_relevant,
        citations_supported=citations_supported,
        repaired=result.repaired,
        final_success=final_success,
    )