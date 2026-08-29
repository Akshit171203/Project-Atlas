from app.services.nli import nli_provider


def main():

    tests = [
        (
            "Light roasts preserve brighter acidity and "
            "origin-specific fruit or floral notes.",
            "Light roasts preserve brighter acidity.",
        ),
        (
            "Light roasts preserve brighter acidity and "
            "origin-specific fruit or floral notes.",
            "Light roasts contain more caffeine than dark roasts.",
        ),
        (
            "Light roasts preserve brighter acidity and "
            "origin-specific fruit or floral notes.",
            "Coffee is grown on Mars.",
        ),
    ]

    for premise, hypothesis in tests:

        result = nli_provider.predict(
            premise=premise,
            hypothesis=hypothesis,
        )

        print("=" * 80)
        print("PREMISE:")
        print(premise)

        print()
        print("HYPOTHESIS:")
        print(hypothesis)

        print()
        print("RESULT:")
        print(result)


if __name__ == "__main__":
    main()