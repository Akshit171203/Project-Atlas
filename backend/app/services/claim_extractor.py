import re
from app.schemas.claims import Claim


CITATION_PATTERN = re.compile(
    r"\[S\d+\]"
)


def _normalize_markdown(
    answer: str,
) -> list[str]:

    lines = answer.splitlines()

    normalized = []

    current = ""

    for line in lines:

        line = line.strip()

        if not line:
            if current:
                normalized.append(current)
                current = ""

            continue

        # Markdown bullet
        line = re.sub(
            r"^[-*+]\s+",
            "",
            line,
        )

        # Markdown heading
        line = re.sub(
            r"^#+\s+",
            "",
            line,
        )

        # Start a new bullet/paragraph if we already
        # have content and this line has a citation.
        if current and CITATION_PATTERN.search(line):

            current += " " + line

            normalized.append(current)

            current = ""

        else:

            if current:
                current += " " + line
            else:
                current = line

    if current:
        normalized.append(current)

    return normalized


def extract_claims(
    answer: str,
) -> list[Claim]:

    claims = []

    blocks = _normalize_markdown(answer)

    for block in blocks:

        if not CITATION_PATTERN.search(block):
            continue

        sentences = re.split(
            r"(?<=[.!?])\s+",
            block,
        )

        for sentence in sentences:

            citations = CITATION_PATTERN.findall(
                sentence
            )

            if not citations:
                continue

            claim = CITATION_PATTERN.sub(
                "",
                sentence,
            ).strip()

            claim = re.sub(
                r"\s+([.,!?])",
                r"\1",
                claim,
            )

            if not claim:
                continue

            source_ids = [
                citation.strip("[]")
                for citation in citations
            ]

            claims.append(
                Claim(
                    claim_id=len(claims) + 1,
                    text=claim,
                    source_ids=source_ids,
                )
            )

    return claims