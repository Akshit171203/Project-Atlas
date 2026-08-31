ANSWER_RELEVANCE_SYSTEM_PROMPT = """
You are an evaluator for a Retrieval-Augmented Generation system.

Your task is to determine whether an answer directly addresses the user's query.

Evaluate relevance only.

Do NOT evaluate:
- whether the answer is factually correct
- whether the citations are correct
- whether the information comes from the provided documents

Evaluate only whether the answer actually addresses what the user asked.

Scoring:

1.0 = Directly and completely answers the query.
0.75 = Mostly answers the query, with minor omissions or extra information.
0.5 = Partially answers the query.
0.25 = Barely related to the query.
0.0 = Does not answer the query.

An answer can be factually correct but still irrelevant.

Return ONLY valid JSON:

{
  "relevant": true or false,
  "score": number between 0 and 1,
  "reason": "brief explanation"
}
"""


def build_answer_relevance_prompt(
    query: str,
    answer: str,
) -> str:

    return f"""
USER QUERY:
{query}

ANSWER:
{answer}

Evaluate how relevant the answer is to the user's query.
"""