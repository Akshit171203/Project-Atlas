from app.schemas.retrieval import RetrievedChunk
from app.services.rank_fusion import RRFFusion


def chunk(chunk_id: int) -> RetrievedChunk:
    return RetrievedChunk(
        document_id=1,
        filename="test.pdf",
        chunk_id=chunk_id,
        page_number=1,
        chunk_index=chunk_id,
        text=f"Chunk {chunk_id}",
        similarity=0.0,
    )


def main():

    vector_results = [
        chunk(49),
        chunk(50),
        chunk(46),
        chunk(45),
    ]

    keyword_results = [
        chunk(49),
        chunk(48),
        chunk(45),
        chunk(50),
    ]

    fusion = RRFFusion()

    results = fusion.fuse(
        rankings=[
            vector_results,
            keyword_results,
        ],
        top_k=5,
    )

    print("\nRRF RESULTS\n")

    for rank, result in enumerate(
        results,
        start=1,
    ):
        print(
            f"Rank {rank}: "
            f"Chunk {result.chunk_id}"
        )


if __name__ == "__main__":
    main()