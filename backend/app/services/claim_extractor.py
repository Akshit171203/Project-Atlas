import json
from app.schemas.claims import Claim
from app.services.llm import default_llm
from app.prompts.claim_extraction import (
    CLAIM_EXTRACTION_SYSTEM_PROMPT,
    build_claim_extraction_prompt,
)


async def extract_claims(
    answer: str,
) -> list[Claim]:

    user_prompt = build_claim_extraction_prompt(answer)

    response = await default_llm.generate(
        system_prompt=CLAIM_EXTRACTION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    cleaned = response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return []

    claims = []
    for item in data:
        claim_text = item.get("claim")
        sources = item.get("sources", [])

        if claim_text and isinstance(sources, list):
            claims.append(
                Claim(
                    claim_id=len(claims) + 1,
                    text=claim_text,
                    source_ids=sources,
                )
            )

    return claims