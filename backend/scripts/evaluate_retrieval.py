import asyncio

from app.db.session import SessionLocal
from app.services.retrieval import Retriever
from app.services.reranked_retrieval import RerankedRetriever

from app.evals.retrieval_dataset import TEST_CASES
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

            case_id = case["id"]
            query = case["query"]
            relevant_chunks = case["relevant_chunks"]
            document_id = case.get("document_id")

            print(f"CASE: {case_id}\n")

            if not relevant_chunks:
                print("SKIPPED FROM RETRIEVAL METRICS — NO GROUND TRUTH\n")
                continue

            # -------------------------
            # Vector retrieval
            # -------------------------

            vector_results = await vector_retriever.retrieve(
                session=session,
                query=query,
                top_k=10,
                document_id=document_id,
            )

            vector_ids = [
                chunk.chunk_id
                for chunk in vector_results
            ]

            print("Vector:")
            for rank, chunk_id in enumerate(vector_ids[:5], start=1):
                icon = "✅" if chunk_id in relevant_chunks else "❌"
                print(f"Rank {rank} -> chunk {chunk_id} {icon}")

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
                    document_id=document_id,
                )
            )

            reranked_ids = [
                chunk.chunk_id
                for chunk in reranked_results
            ]

            print("\nReranked:")
            for rank, chunk_id in enumerate(reranked_ids[:5], start=1):
                icon = "✅" if chunk_id in relevant_chunks else "❌"
                print(f"Rank {rank} -> chunk {chunk_id} {icon}")
            
            print("\n----------------------------------------\n")

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

        print("========================================")
        print("RETRIEVAL EVALUATION")
        print("========================================\n")
        print(f"Cases: {len(TEST_CASES)}\n")

        for k in [1, 3, 5]:
            
            vector_recall = (
                sum(vector_recalls[k])
                / len(vector_recalls[k])
            )
            
            reranked_recall = (
                sum(reranked_recalls[k])
                / len(reranked_recalls[k])
            )
            
            print(f"\nRecall@{k}")
            
            print(
                f"Vector only:         "
                f"{vector_recall:.3f}"
            )
            
            print(
                f"Vector + reranker: "
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
            f"Vector only:         "
            f"{vector_mrr:.3f}"
        )
        
        print(
            f"Vector + reranker: "
            f"{reranked_mrr:.3f}"
        )


if __name__ == "__main__":
    asyncio.run(main())