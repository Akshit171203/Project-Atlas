import asyncio

from app.db.session import SessionLocal
from app.evals.rag_dataset import CASES
from app.services.rag import RAGService


async def main():
    rag = RAGService()

    async with SessionLocal() as session:
        for case in CASES:
            if case["name"] != "roast_taste":
                continue

            while True:
                try:
                    print("=" * 80)
                    print("CASE:", case["name"])
                    print("QUERY:", case["query"])
                    print("EXPECTED ANSWERABLE:", case["answerable"])

                    result = await rag.answer(
                        session=session,
                        query=str(case["query"]),
                    )

                    print("ACTUAL ANSWER:", result.answer)
                    print("REPAIRED:", result.repaired)
                    print(
                        "ALL CITATIONS SUPPORTED:",
                        result.verification.all_supported if result.verification else None,
                    )

                    if result.repaired and result.initial_verification:
                        print()
                        print("INITIAL VERIFICATION FAILURES:")
                        for item in result.initial_verification.failed:
                            print(f"- {item.claim}")
                            print(f"  SOURCE: {item.source_id}")
                            print(f"  LABEL: {item.label}")
                            print(f"  SCORE: {item.score:.4f}")

                    print(
                        "FINAL ANSWER:",
                        result.answer,
                    )
                    break
                except Exception as e:
                    if "429" in str(e):
                        print("Rate limited, sleeping for 60s...")
                        await asyncio.sleep(60)
                    else:
                        raise e


if __name__ == "__main__":
    asyncio.run(main())
