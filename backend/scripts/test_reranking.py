import asyncio
import sys
from pathlib import Path

# Add backend directory to path to allow importing app module
sys.path.append(str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.services.reranked_retrieval import RerankedRetriever


async def main():

    retriever = RerankedRetriever()

    queries = [
        "How does roast level affect the taste of coffee?",
        "Why do darker and lighter roasted beans taste different?",
        "What are the symptoms of a computer virus?",
        "How many calories are in a cup of coffee?",
    ]

    async with SessionLocal() as session:

        for query in queries:

            results = await retriever.retrieve(
                session=session,
                query=query,
                candidate_k=10,
                top_k=5,
            )

            print("\n")
            print("=" * 100)
            print(f"QUERY: {query}")
            print("=" * 100)

            for rank, chunk in enumerate(
                results,
                start=1,
            ):
                print(
                    f"\nRank: {rank}"
                )

                print(
                    f"Chunk: {chunk.chunk_id}"
                )

                print(
                    f"Page: {chunk.page_number}"
                )

                print(
                    f"Vector similarity: "
                    f"{chunk.similarity:.4f}"
                )

                if chunk.rerank_score is not None:
                    print(
                        f"Rerank score: "
                        f"{chunk.rerank_score:.4f}"
                    )

                print(
                    f"Text: {chunk.text[:400]}"
                )


if __name__ == "__main__":
    asyncio.run(main())