import re


CITATION_PATTERN = re.compile(
    r"\[S(\d+)\]"
)


def extract_citations(
    answer: str,
) -> list[str]:

    matches = CITATION_PATTERN.findall(answer)

    return [
        f"S{number}"
        for number in matches
    ]