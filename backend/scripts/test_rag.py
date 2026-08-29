import asyncio

from app.db.session import SessionLocal
from app.services.rag import RAGService


async def main():

    queries = [
        "Why does roast level affect the taste of coffee?",
        "What are the symptoms of a computer virus?",
    ]

    rag = RAGService()

    async with SessionLocal() as session:
        for query in queries:
            print("=" * 100)
            print(f"QUERY: {query}")
            print("=" * 100)
            
            result = await rag.answer(
                session=session,
                query=query,
            )
        
            print()
            print("ANSWER:")
            print(result.answer)
        
            print()
            print("REPAIR STATUS:")
            print("Repaired:", result.repaired)
            print(
                "All supported:",
                result.verification.all_supported,
            )
        
            if result.verification.verifications:
                print()
                print("CITATION VERIFICATION:")
                for verification in result.verification.verifications:
                    print()
                    print("CLAIM:", verification.claim)
                    print("SOURCE:", verification.source_id)
                    print("LABEL:", verification.label)
                    print(
                        "ENTAILMENT SCORE:",
                        f"{verification.score:.4f}",
                    )
                    print("SUPPORTED:", verification.supported)
            print("\n")

if __name__ == "__main__":
    asyncio.run(main())