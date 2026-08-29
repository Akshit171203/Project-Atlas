REPAIR_SYSTEM_PROMPT = """
You are a citation repair assistant.

You will receive:
1. An answer generated from retrieved sources.
2. The sources available to the answer.
3. Claims whose citations failed verification.

Your task is to repair the answer.

Rules:

1. Use ONLY the provided sources.
2. Do not introduce outside knowledge.
3. Remove or rewrite unsupported claims.
4. Use only valid source IDs such as [S1], [S2].
5. Every factual claim must have an appropriate citation.
6. Do not invent citations.
7. Preserve supported parts of the original answer.
8. If a failed claim cannot be supported by the provided
   sources, remove it rather than guessing.
9. Return only the repaired answer.
"""


def build_repair_prompt(
    answer: str,
    context: str,
    failed_claims: list[str],
) -> str:

    failed = "\n".join(
        f"- {claim}"
        for claim in failed_claims
    )

    return f"""
ORIGINAL ANSWER:

{answer}


AVAILABLE SOURCES:

{context}


FAILED CLAIMS:

{failed}


Repair the original answer so that every factual claim is
supported by the available sources.
"""