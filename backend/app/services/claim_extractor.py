import re


def extract_claims(
    answer: str,
) -> list[tuple[str, list[str]]]:

    claims = []

    sentences = re.split(
        r"(?<=[.!?])\s+",
        answer.strip(),
    )

    for sentence in sentences:

        citations = re.findall(
            r"\[S\d+\]",
            sentence,
        )

        if not citations:
            continue

        clean_citations = [
            citation.strip("[]")
            for citation in citations
        ]

        claim = re.sub(
            r"\[S\d+\]",
            "",
            sentence,
        ).strip()

        if claim:
            claims.append(
                (
                    claim,
                    clean_citations,
                )
            )

    return claims