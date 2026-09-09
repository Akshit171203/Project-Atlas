from app.prompts.citation_repair import (
    REPAIR_SYSTEM_PROMPT,
    build_repair_prompt,
)
from app.services.llm import default_llm


class AnswerRepairer:

    def __init__(self):
        self.llm = default_llm

    async def repair(
        self,
        answer: str,
        context: str,
        failed_claims: list[str],
    ) -> str:

        prompt = build_repair_prompt(
            answer=answer,
            context=context,
            failed_claims=failed_claims,
        )

        return await self.llm.generate(
            system_prompt=REPAIR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )