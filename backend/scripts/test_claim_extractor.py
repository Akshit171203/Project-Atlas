import asyncio
from app.services.claim_extractor import extract_claims


async def main():

    answer = """
Roast level affects coffee flavor.

* Light roasts preserve brighter acidity and
  fruit or floral notes [S1].

* Dark roasts develop heavier, smokier and
  more bitter flavors [S1].

* Roasting triggers the Maillard reaction
  and caramelization [S4].
"""

    claims = await extract_claims(answer)

    print("=" * 80)
    print("EXTRACTED CLAIMS")
    print("=" * 80)

    for claim in claims:

        print()
        print(f"CLAIM [{claim.claim_id}]:", claim.text)
        print("SOURCES:", claim.source_ids)


if __name__ == "__main__":
    asyncio.run(main())