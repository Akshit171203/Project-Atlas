import asyncio

from app.db.session import SessionLocal
from app.services.retrieval import Retriever
from app.services.reranked_retrieval import RerankedRetriever

from typing import TypedDict

class TestCase(TypedDict):
    query: str
    relevant_chunks: list[int]

TEST_CASES: list[TestCase] = [
    {
        "query": "How does roast level affect the taste of coffee?",
        "relevant_chunks": [49],
    },

    {
        "query": "Why do darker and lighter roasted beans taste different?",
        "relevant_chunks": [49],
    },

    {
        "query": "How much caffeine is in a 240-milliliter cup of coffee?",
        "relevant_chunks": [48],
    },

    {
        "query": "What chemical reactions occur during coffee roasting?",
        "relevant_chunks": [46],
    },

    {
        "query": "What happens to coffee beans during roasting?",
        "relevant_chunks": [46],
    },

    {
        "query": "Where did coffee originate?",
        "relevant_chunks": [42],
    },

    {
        "query": "Which coffee species dominate commercial production?",
        "relevant_chunks": [42],
    },

    {
        "query": "Why is Arabica more expensive to cultivate?",
        "relevant_chunks": [43],
    },
]
def recall_at_k(
    retrieved_chunk_ids: list[int],
    relevant_chunk_ids: list[int],
    k: int,
) -> float:

    retrieved = set(retrieved_chunk_ids[:k])
    relevant = set(relevant_chunk_ids)

    return 1.0 if retrieved.intersection(relevant) else 0.0

def reciprocal_rank(
    retrieved_chunk_ids: list[int],
    relevant_chunk_ids: list[int],
) -> float:

    relevant = set(relevant_chunk_ids)

    for rank, chunk_id in enumerate(
        retrieved_chunk_ids,
        start=1,
    ):
        if chunk_id in relevant:
            return 1.0 / rank

    return 0.0

async def main():

    vector_retriever = Retriever()
    reranked_retriever = RerankedRetriever()

    async with SessionLocal() as session:

        vector_rr = []
        reranked_rr = []

        vector_recalls = {
            1: [],
            3: [],
            5: [],
        }

        reranked_recalls = {
            1: [],
            3: [],
            5: [],
        }

        for case in TEST_CASES:

            query = case["query"]
            relevant_chunks = case["relevant_chunks"]

            print("\n")
            print("=" * 100)
            print(f"QUERY: {query}")
            print(f"GROUND TRUTH: {relevant_chunks}")
            print("=" * 100)

            # -------------------------
            # Vector retrieval
            # -------------------------

            vector_results = await vector_retriever.retrieve(
                session=session,
                query=query,
                top_k=10,
            )

            vector_ids = [
                chunk.chunk_id
                for chunk in vector_results
            ]

            print("\nVector Search:")
            print(vector_ids)

            for k in [1, 3, 5]:

                score = recall_at_k(
                    vector_ids,
                    relevant_chunks,
                    k,
                )

                vector_recalls[k].append(score)

            vector_rr.append(
                reciprocal_rank(
                    vector_ids,
                    relevant_chunks,
                )
            )

            # -------------------------
            # Reranked retrieval
            # -------------------------

            reranked_results = (
                await reranked_retriever.retrieve(
                    session=session,
                    query=query,
                    candidate_k=10,
                    top_k=5,
                )
            )

            reranked_ids = [
                chunk.chunk_id
                for chunk in reranked_results
            ]

            print("\nReranked Search:")
            print(reranked_ids)

            for k in [1, 3, 5]:

                score = recall_at_k(
                    reranked_ids,
                    relevant_chunks,
                    k,
                )

                reranked_recalls[k].append(score)

            reranked_rr.append(
                reciprocal_rank(
                    reranked_ids,
                    relevant_chunks,
                )
            )

        # -------------------------
        # Final metrics
        # -------------------------

        print("\n")
        print("=" * 100)
        print("FINAL RESULTS")
        print("=" * 100)

        for k in [1, 3, 5]:

            vector_recall = (
                sum(vector_recalls[k])
                / len(vector_recalls[k])
            )

            reranked_recall = (
                sum(reranked_recalls[k])
                / len(reranked_recalls[k])
            )

            print(
                f"\nRecall@{k}"
            )

            print(
                f"Vector only:     "
                f"{vector_recall:.3f}"
            )

            print(
                f"With reranking:  "
                f"{reranked_recall:.3f}"
            )

        vector_mrr = (
            sum(vector_rr)
            / len(vector_rr)
        )

        reranked_mrr = (
            sum(reranked_rr)
            / len(reranked_rr)
        )

        print("\nMRR")

        print(
            f"Vector only:     "
            f"{vector_mrr:.3f}"
        )

        print(
            f"With reranking:  "
            f"{reranked_mrr:.3f}"
        )


if __name__ == "__main__":
    asyncio.run(main())