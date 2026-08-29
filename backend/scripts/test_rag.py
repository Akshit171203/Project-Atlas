import asyncio

from app.db.session import SessionLocal
from app.services.rag import RAGService


async def main():

    query = "Why does roast level affect the taste of coffee?"

    rag = RAGService()

    async with SessionLocal() as session:

        result = await rag.answer(
            session=session,
            query=query,
        )

    print("=" * 100)
    print("ANSWER")
    print("=" * 100)

    print(result.answer)

    print()
    print("=" * 100)
    print("REPAIR STATUS")
    print("=" * 100)

    print("Repaired:", result.repaired)
    print(
        "All supported:",
        result.verification.all_supported,
    )

    print()
    print("=" * 100)
    print("CITATION VERIFICATION")
    print("=" * 100)

    for verification in result.verification.verifications:

        print()
        print("CLAIM:", verification.claim)
        print("SOURCE:", verification.source_id)
        print("LABEL:", verification.label)
        print(
            "ENTAILMENT SCORE:",
            f"{verification.score:.4f}",
        )
        print("SUPPORTED:", verification.supported)


if __name__ == "__main__":
    asyncio.run(main())