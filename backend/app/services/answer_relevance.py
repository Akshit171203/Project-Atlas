import json

from app.prompts.answer_relevance import (
    ANSWER_RELEVANCE_SYSTEM_PROMPT,
    build_answer_relevance_prompt,
)
from app.schemas.evaluation import AnswerRelevanceResult
from app.services.llm import gemini_provider


class AnswerRelevanceEvaluator:

    async def evaluate(
        self,
        query: str,
        answer: str,
    ) -> AnswerRelevanceResult:

        prompt = build_answer_relevance_prompt(
            query=query,
            answer=answer,
        )

        response = await gemini_provider.generate(
            user_prompt=prompt,
            system_prompt=ANSWER_RELEVANCE_SYSTEM_PROMPT,
        )

        data = json.loads(response)

        return AnswerRelevanceResult.model_validate(data)


answer_relevance_evaluator = AnswerRelevanceEvaluator()