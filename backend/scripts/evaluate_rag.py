import asyncio

from app.db.session import SessionLocal
from app.evals.rag_dataset import CASES
from app.evals.rag_evaluation import evaluate_case


async def main():

    results = []

    async with SessionLocal() as session:

        for case in CASES:

            print("=" * 80)
            print(f"CASE: {case['name']}")
            print(f"QUERY: {case['query']}")
            print(
                f"EXPECTED ANSWERABLE: "
                f"{case['answerable']}"
            )

            result = await evaluate_case(
                session=session,
                case=case,
            )

            results.append(result)

            print(
                f"ACTUAL ANSWERABLE: "
                f"{result.actual_answerable}"
            )

            print(
                f"RETRIEVAL HIT: "
                f"{result.retrieval_hit}"
            )

            print(
                f"ANSWER RELEVANT: "
                f"{result.answer_relevant}"
            )

            print(
                f"CITATIONS SUPPORTED: "
                f"{result.citations_supported}"
            )

            print(
                f"REPAIRED: "
                f"{result.repaired}"
            )

            print(
                f"FINAL SUCCESS: "
                f"{result.final_success}"
            )

    total = len(results)

    successful = sum(
        result.final_success
        for result in results
    )

    repaired = sum(
        result.repaired
        for result in results
    )

    print()
    print("=" * 80)
    print("END-TO-END RAG EVALUATION")
    print("=" * 80)

    print(f"Cases: {total}")

    print(
        f"Successful: "
        f"{successful}/{total}"
    )

    print(
        f"Success rate: "
        f"{successful / total:.3f}"
    )

    print(
        f"Repair rate: "
        f"{repaired / total:.3f}"
    )


if __name__ == "__main__":
    asyncio.run(main())