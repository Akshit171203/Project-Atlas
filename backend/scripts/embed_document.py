import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import app.db.base  # Ensures all models are registered

from app.db.session import SessionLocal
from app.services.embedding_pipeline import EmbeddingPipeline


async def main():
    pipeline = EmbeddingPipeline()

    async with SessionLocal() as session:
        count = await pipeline.embed_document(
            session=session,
            document_id=1,
        )

    print(f"Created {count} embeddings")


if __name__ == "__main__":
    asyncio.run(main())