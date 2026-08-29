import asyncio

from app.db.session import SessionLocal
from app.evals.answerability_dataset import CASES
from app.services.evidence_gate import EvidenceGate
from app.services.reranked_retrieval import RerankedRetriever


async def main():

    retriever = RerankedRetriever()
    gate = EvidenceGate(
        min_rerank_score=0.0
    )

    correct = 0

    async with SessionLocal() as session:

        for case in CASES:

            chunks = await retriever.retrieve(
                session=session,
                query=case["query"],
                candidate_k=10,
                top_k=5,
            )

            predicted = gate.is_answerable(
                chunks
            )

            expected = case["answerable"]

            is_correct = predicted == expected

            if is_correct:
                correct += 1

            best_score = max(
                chunk.rerank_score
                for chunk in chunks
                if chunk.rerank_score is not None
            )

            print("=" * 80)
            print("CASE:", case["name"])
            print("EXPECTED:", expected)
            print("PREDICTED:", predicted)
            print("BEST RERANK SCORE:", best_score)
            print(
                "STATUS:",
                "✅" if is_correct else "❌",
            )

    print()
    print("=" * 80)
    print("EVIDENCE GATE ACCURACY")
    print("=" * 80)

    print(
        f"{correct}/{len(CASES)} "
        f"= {correct / len(CASES):.3f}"
    )


if __name__ == "__main__":
    asyncio.run(main())