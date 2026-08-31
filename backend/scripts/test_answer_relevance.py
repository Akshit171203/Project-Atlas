import asyncio
from typing import TypedDict

from app.services.answer_relevance import (
    answer_relevance_evaluator,
)


class TestCase(TypedDict):
    name: str
    query: str
    answer: str
    expected: bool


CASES: list[TestCase] = [
    {
        "name": "direct_answer",
        "query": "Why does roast level affect the taste of coffee?",
        "answer": (
            "Light roasts preserve brighter acidity and fruit or floral "
            "notes, while dark roasts develop heavier, smokier, and more "
            "bitter flavors."
        ),
        "expected": True,
    },
    {
        "name": "irrelevant_answer",
        "query": "Why does roast level affect the taste of coffee?",
        "answer": (
            "Coffee originated in the Ethiopian highlands and is now "
            "cultivated in many countries."
        ),
        "expected": False,
    },
    {
        "name": "partial_answer",
        "query": "Why does roast level affect the taste of coffee?",
        "answer": (
            "Dark roasts generally develop heavier and more bitter flavors."
        ),
        "expected": True,
    },
    {
        "name": "unrelated_answer",
        "query": "Why does roast level affect the taste of coffee?",
        "answer": (
            "A typical 240-milliliter cup of brewed coffee contains "
            "80 to 100 milligrams of caffeine."
        ),
        "expected": False,
    },
]


async def main():

    for case in CASES:

        result = await answer_relevance_evaluator.evaluate(
            query=case["query"],
            answer=case["answer"],
        )

        print("=" * 80)
        print(f"CASE: {case['name']}")
        print(f"EXPECTED: {case['expected']}")
        print(f"PREDICTED: {result.relevant}")
        print(f"SCORE: {result.score:.4f}")
        print(f"REASON: {result.reason}")

        status = (
            "✅"
            if result.relevant == case["expected"]
            else "❌"
        )

        print(f"STATUS: {status}")


if __name__ == "__main__":
    asyncio.run(main())