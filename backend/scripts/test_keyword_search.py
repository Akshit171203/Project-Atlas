import asyncio

from app.db.session import SessionLocal
from app.repositories.embedding_repository import EmbeddingRepository

async def main():
    repository = EmbeddingRepository()

    query = "Why does roast level affect the taste of coffee?"

    async with SessionLocal() as session:
        results = await repository.search_keyword(
            session=session,
            query=query,
            top_k=5,
        )

    print(f"\nQuery: {query}\n")

    for rank, (chunk, score) in enumerate(results, start=1):
        print("=" * 80)
        print(f"Rank: {rank}")
        print(f"Chunk: {chunk.id}")
        print(f"Page: {chunk.page_number}")
        print(f"Keyword score: {score:.4f}")
        print(f"Text: {chunk.text[:500]}")


if __name__ == "__main__":
    asyncio.run(main())
