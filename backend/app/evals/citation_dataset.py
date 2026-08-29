CASES = [
    {
        "name": "supported_claim",
        "claim": "Light roasts preserve brighter acidity.",
        "source": (
            "Light roasts preserve brighter acidity "
            "and origin-specific fruit or floral notes."
        ),
        "expected": "entailment",
    },
    {
        "name": "wrong_citation",
        "claim": "Light roasts contain more caffeine than dark roasts.",
        "source": (
            "Light roasts preserve brighter acidity "
            "and origin-specific fruit or floral notes."
        ),
        "expected": "neutral",
    },
    {
        "name": "contradiction",
        "claim": "Coffee is grown on Mars.",
        "source": (
            "Coffee comes from the seeds of flowering "
            "shrubs belonging to the genus Coffea."
        ),
        "expected": "contradiction",
    },
    {
        "name": "maillard_supported",
        "claim": "Roasting triggers the Maillard reaction.",
        "source": (
            "Roasting triggers a cascade of chemical "
            "transformations, most notably the Maillard reaction."
        ),
        "expected": "entailment",
    },
]