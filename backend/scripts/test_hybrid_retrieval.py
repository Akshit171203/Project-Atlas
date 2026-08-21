import asyncio

from app.db.session import SessionLocal
from app.services.hybrid_retrieval import HybridRetriever


async def main():

    query = "Why does roast level affect the taste of coffee?"

    retriever = HybridRetriever()

    async with SessionLocal() as session:

        results = await retriever.retrieve(
            session=session,
            query=query,
            candidate_k=20,
            top_k=5,
        )

    print("=" * 100)
    print(f"QUERY: {query}")
    print("=" * 100)

    for rank, chunk in enumerate(
        results,
        start=1,
    ):

        print()
        print(f"Rank: {rank}")
        print(f"Chunk: {chunk.chunk_id}")
        print(f"Page: {chunk.page_number}")
        print(f"Rerank score: {chunk.rerank_score:.4f}")
        print(f"Text: {chunk.text[:500]}")


if __name__ == "__main__":
    asyncio.run(main())