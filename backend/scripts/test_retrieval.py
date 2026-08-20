import asyncio
import sys
from pathlib import Path

# Add backend directory to path to allow importing app module
sys.path.append(str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.services.retrieval import Retriever


async def main():

    retriever = Retriever()

    query = "How many calories are in a cup of coffee?"

    async with SessionLocal() as session:

        results = await retriever.retrieve(
            session=session,
            query=query,
            top_k=5,
        )

    print(f"\nQuery: {query}\n")

    for rank, chunk in enumerate(
        results,
        start=1,
    ):

        print("=" * 80)
        print(f"Rank: {rank}")
        print(f"Document ID: {chunk.document_id}")
        print(f"Filename: {chunk.filename}")
        print(f"Chunk ID: {chunk.chunk_id}")
        print(f"Page: {chunk.page_number}")
        print(f"Similarity: {chunk.similarity:.4f}")
        print()
        print(chunk.text[:500])
        print()


if __name__ == "__main__":
    asyncio.run(main())