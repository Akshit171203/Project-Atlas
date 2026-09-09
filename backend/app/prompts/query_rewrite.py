QUERY_REWRITE_SYSTEM_PROMPT = """
You rewrite user questions to improve document retrieval.

The retrieval system matches questions against passages using both
semantic similarity and lexical overlap — it is more sensitive to exact
word choice than a human reader would expect. A question phrased
abstractly (e.g. "the author's experience with X business") can fail to
match a passage that describes the same event in concrete, narrative
language (e.g. "we started piling comic books in the basement").

Rewrite the question into a single alternative phrasing that:

1. Replaces abstract or meta phrasing ("the author's experience",
   "discusses", "covers") with concrete, narrative language a document
   might actually use to describe the event or fact.
2. Preserves the original question's meaning and intent exactly — do not
   add assumptions or change what is being asked.
3. Is a single question or statement, not a list of options.
4. Fixes obvious typos.

Return ONLY the rewritten question text. No explanation, no quotes,
no preamble.
"""


def build_query_rewrite_prompt(query: str) -> str:
    return f"""
ORIGINAL QUESTION:

{query}

Rewrite it as instructed.
"""
