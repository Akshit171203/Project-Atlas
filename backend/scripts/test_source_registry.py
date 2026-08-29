from app.schemas.retrieval import RetrievedChunk
from app.services.source_registry import SourceRegistry


def main():

    chunks = [
        RetrievedChunk(
            document_id=4,
            filename="sample_coffee_report.pdf",
            chunk_id=49,
            page_number=2,
            chunk_index=7,
            text="Light roasts preserve brighter acidity.",
            similarity=0.8,
        ),
        RetrievedChunk(
            document_id=4,
            filename="sample_coffee_report.pdf",
            chunk_id=46,
            page_number=1,
            chunk_index=4,
            text="Roasting triggers the Maillard reaction.",
            similarity=0.7,
        ),
    ]

    registry = SourceRegistry(chunks)

    for source_id, chunk in registry.all().items():

        print(
            source_id,
            "->",
            f"chunk={chunk.chunk_id}",
            f"page={chunk.page_number}",
        )


if __name__ == "__main__":
    main()