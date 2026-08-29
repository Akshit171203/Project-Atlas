from app.services.nli import nli_provider
from app.evals.citation_dataset import CASES


def main():

    correct = 0

    print("=" * 100)
    print("CITATION VERIFICATION EVALUATION")
    print("=" * 100)

    for case in CASES:

        result = nli_provider.predict(
            premise=case["source"],
            hypothesis=case["claim"],
        )

        predicted = result["label"]
        expected = case["expected"]

        is_correct = predicted == expected

        if is_correct:
            correct += 1

        print()
        print(f"CASE: {case['name']}")
        print(f"Expected: {expected}")
        print(f"Predicted: {predicted}")
        print(
            f"Status: {'✅' if is_correct else '❌'}"
        )

        print(
            "Scores:",
            {
                key: round(value, 4)
                for key, value in result["scores"].items()
            },
        )

    accuracy = correct / len(CASES)

    print()
    print("=" * 100)
    print("RESULT")
    print("=" * 100)
    print(
        f"Accuracy: {accuracy:.3f}"
    )


if __name__ == "__main__":
    main()