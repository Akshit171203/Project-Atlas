import json

from app.prompts.answer_relevance import (
    ANSWER_RELEVANCE_SYSTEM_PROMPT,
    build_answer_relevance_prompt,
)
from app.schemas.evaluation import AnswerRelevanceResult
from app.services.llm import default_llm


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

        response = await default_llm.generate(
            user_prompt=prompt,
            system_prompt=ANSWER_RELEVANCE_SYSTEM_PROMPT,
        )

        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        data = json.loads(cleaned.strip())

        return AnswerRelevanceResult.model_validate(data)


answer_relevance_evaluator = AnswerRelevanceEvaluator()