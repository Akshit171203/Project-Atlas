import asyncio
from app.schemas.retrieval import RetrievedChunk
from app.services.citation_verifier import CitationVerifier
from app.services.source_registry import SourceRegistry


async def main():

    chunks = [
        RetrievedChunk(
            document_id=4,
            filename="sample_coffee_report.pdf",
            chunk_id=49,
            page_number=2,
            chunk_index=7,
            text=(
                "Light roasts preserve brighter acidity "
                "and origin-specific fruit or floral notes."
            ),
            similarity=0.8,
        ),
        RetrievedChunk(
            document_id=4,
            filename="sample_coffee_report.pdf",
            chunk_id=46,
            page_number=1,
            chunk_index=4,
            text=(
                "Roasting triggers chemical transformations "
                "including the Maillard reaction and "
                "caramelization."
            ),
            similarity=0.7,
        ),
    ]

    registry = SourceRegistry(chunks)

    verifier = CitationVerifier()

    tests = [
        (
            "Light roasts preserve brighter acidity.",
            "S1",
        ),
        (
            "The Maillard reaction occurs during roasting.",
            "S2",
        ),
        (
            "Coffee is grown on Mars.",
            "S1",
        ),
        (
            "Light roasts contain more caffeine than dark roasts.",
            "S1",
        ),
    ]

    for claim, source_id in tests:
        print("=" * 80)
        print(f"CLAIM: {claim}")

        result = verifier.verify(
            claim=claim,
            source_id=source_id,
            registry=registry,
        )

        print(
            "LABEL:",
            result.label,
        )

        print(
            "ENTAILMENT SCORE:",
            f"{result.score:.4f}",
        )

        print(
            "SUPPORTED:",
            result.supported,
        )


if __name__ == "__main__":
    asyncio.run(main())