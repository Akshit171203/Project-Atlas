CASES = [

    {
        "name": "roast_taste",
        "query": "Why does roast level affect the taste of coffee?",
        "expected_answer": (
            "Light roasts preserve brighter acidity and "
            "origin-specific fruit or floral notes, while "
            "dark roasts develop heavier, smokier and more "
            "bitter flavors."
        ),
        "answerable": True,
    },

    {
        "name": "coffee_caffeine",
        "query": (
            "How much caffeine is in a 240-milliliter "
            "cup of coffee?"
        ),
        "expected_answer": (
            "A typical 240-milliliter cup of brewed coffee "
            "contains between 80 and 100 milligrams of caffeine."
        ),
        "answerable": True,
    },

    {
        "name": "maillard",
        "query": (
            "What role does the Maillard reaction play "
            "in coffee roasting?"
        ),
        "expected_answer": (
            "It combines amino acids and reducing sugars "
            "under heat and produces new aromatic compounds."
        ),
        "answerable": True,
    },

    {
        "name": "arabica_robusta",
        "query": (
            "How do arabica and robusta differ?"
        ),
        "expected_answer": (
            "Arabica is comparatively mild and aromatic, "
            "while robusta contains substantially more "
            "caffeine and is easier to cultivate."
        ),
        "answerable": True,
    },

    {
        "name": "coffee_origins",
        "query": (
            "Where did coffee originate?"
        ),
        "expected_answer": (
            "Coffee is native to the highlands of Ethiopia."
        ),
        "answerable": True,
    },

    {
        "name": "computer_virus",
        "query": (
            "What are the symptoms of a computer virus?"
        ),
        "expected_answer": None,
        "answerable": False,
    },

    {
        "name": "python_bst",
        "query": (
            "How do I implement a binary search tree in Python?"
        ),
        "expected_answer": None,
        "answerable": False,
    },

]