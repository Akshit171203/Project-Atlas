import asyncio

from app.db.session import SessionLocal
from app.evals.answerability_dataset import CASES
from app.services.reranked_retrieval import RerankedRetriever


async def main():

    retriever = RerankedRetriever()

    async with SessionLocal() as session:

        for case in CASES:

            chunks = await retriever.retrieve(
                session=session,
                query=str(case["query"]),
                candidate_k=10,
                top_k=5,
            )

            print("=" * 100)
            print("CASE:", case["name"])
            print("QUERY:", case["query"])
            print("EXPECTED ANSWERABLE:", case["answerable"])

            print()

            for index, chunk in enumerate(chunks, start=1):

                print(
                    f"Rank {index}: "
                    f"chunk={chunk.chunk_id} "
                    f"similarity={chunk.similarity:.4f} "
                    f"rerank={chunk.rerank_score:.4f}"
                )


if __name__ == "__main__":
    asyncio.run(main())