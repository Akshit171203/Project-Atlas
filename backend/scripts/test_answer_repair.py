import asyncio

from app.db.session import SessionLocal
from app.services.answer_repairer import AnswerRepairer
from app.services.answer_verifier import AnswerVerifier
from app.services.context_builder import ContextBuilder
from app.services.context_formatter import ContextFormatter
from app.services.reranked_retrieval import RerankedRetriever
from app.services.source_registry import SourceRegistry


async def main():

    query = "Why does roast level affect the taste of coffee?"

    bad_answer = """
Light roasts preserve brighter acidity and fruit or
floral notes [S4].

Dark roasts are grown exclusively in Brazil [S1].

Roasting triggers the Maillard reaction [S1].
"""

    retriever = RerankedRetriever()

    async with SessionLocal() as session:
        chunks = await retriever.retrieve(
            session=session,
            query=query,
            candidate_k=10,
            top_k=5,
        )

    registry = SourceRegistry(chunks)

    verifier = AnswerVerifier()

    before = verifier.verify(
        answer=bad_answer,
        registry=registry,
    )

    print("=" * 100)
    print("BEFORE REPAIR")
    print("=" * 100)

    for item in before.verifications:
        print(
            item.claim,
            "->",
            item.label,
            item.supported,
        )

    context_builder = ContextBuilder()
    context_formatter = ContextFormatter()

    context = context_builder.build(
        query=query,
        chunks=chunks,
    )

    formatted_context = context_formatter.format(
        context
    )

    failed_claims = [
        item.claim
        for item in before.failed
    ]

    repairer = AnswerRepairer()

    repaired_answer = await repairer.repair(
        answer=bad_answer,
        context=formatted_context,
        failed_claims=failed_claims,
    )

    print()
    print("=" * 100)
    print("REPAIRED ANSWER")
    print("=" * 100)
    print(repaired_answer)

    after = verifier.verify(
        answer=repaired_answer,
        registry=registry,
    )

    print()
    print("=" * 100)
    print("AFTER REPAIR")
    print("=" * 100)

    for item in after.verifications:
        print(
            item.claim,
            "->",
            item.label,
            item.supported,
        )

    print()
    print(
        "ALL SUPPORTED:",
        after.all_supported,
    )


if __name__ == "__main__":
    asyncio.run(main())