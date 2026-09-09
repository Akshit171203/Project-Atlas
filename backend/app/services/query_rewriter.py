from app.prompts.query_rewrite import (
    QUERY_REWRITE_SYSTEM_PROMPT,
    build_query_rewrite_prompt,
)
from app.services.llm import default_llm


class QueryRewriter:

    async def rewrite(self, query: str) -> str | None:

        prompt = build_query_rewrite_prompt(query)

        response = await default_llm.generate(
            system_prompt=QUERY_REWRITE_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        rewritten = response.strip().strip('"')

        # A rewrite that came back empty or identical to the original
        # adds no retrieval value — treat it as "no rewrite available"
        # rather than retrieving twice for the same query.
        if not rewritten or rewritten.lower() == query.strip().lower():
            return None

        return rewritten


query_rewriter = QueryRewriter()
