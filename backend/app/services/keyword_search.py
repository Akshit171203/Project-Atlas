import re

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "does",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "why",
    "with",
}

def prepare_keyword_query(query: str) -> str:
    words = re.findall(r"\b[a-zA-Z0-9]+\b", query.lower())

    keywords = [
        word
        for word in words
        if word not in STOP_WORDS
    ]

    return " OR ".join(keywords)
