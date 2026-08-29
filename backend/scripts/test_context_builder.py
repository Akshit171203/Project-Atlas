import asyncio

from app.db.session import SessionLocal
from app.services.context_builder import ContextBuilder
from app.services.context_formatter import ContextFormatter
from app.services.reranked_retrieval import RerankedRetriever


async def main():

    query = "Why does roast level affect the taste of coffee?"

    retriever = RerankedRetriever()

    async with SessionLocal() as session:

        chunks = await retriever.retrieve(
            session=session,
            query=query,
            candidate_k=10,
            top_k=5,
        )

    builder = ContextBuilder()

    context = builder.build(
        query=query,
        chunks=chunks,
    )

    formatter = ContextFormatter()

    formatted_context = formatter.format(
        context
    )

    print("=" * 100)
    print("FORMATTED CONTEXT")
    print("=" * 100)
    print(formatted_context)


if __name__ == "__main__":
    asyncio.run(main())