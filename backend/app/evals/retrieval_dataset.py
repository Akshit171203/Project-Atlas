from typing import TypedDict

class TestCase(TypedDict):
    id: str
    query: str
    relevant_chunks: list[int]

TEST_CASES: list[TestCase] = [
    # ---- Existing 8 cases ----
    {
        "id": "roast_taste",
        "query": "How does roast level affect the taste of coffee?",
        "relevant_chunks": [49],
    },
    {
        "id": "dark_light_roast",
        "query": "Why do darker and lighter roasted beans taste different?",
        "relevant_chunks": [49],
    },
    {
        "id": "coffee_caffeine",
        "query": "How much caffeine is in a 240-milliliter cup of coffee?",
        "relevant_chunks": [48],
    },
    {
        "id": "roasting_chemical_reactions",
        "query": "What chemical reactions occur during coffee roasting?",
        "relevant_chunks": [46],
    },
    {
        "id": "roasting_bean_changes",
        "query": "What happens to coffee beans during roasting?",
        "relevant_chunks": [46],
    },
    {
        "id": "coffee_origin",
        "query": "Where did coffee originate?",
        "relevant_chunks": [42],
    },
    {
        "id": "commercial_species",
        "query": "Which coffee species dominate commercial production?",
        "relevant_chunks": [42],
    },
    {
        "id": "arabica_cost",
        "query": "Why is Arabica more expensive to cultivate?",
        "relevant_chunks": [43],
    },

    # ---- Category 1: Direct questions ----
    {
        "id": "discover_coffee",
        "query": "Who discovered coffee according to local legend?",
        "relevant_chunks": [43],
    },
    {
        "id": "bean_belt",
        "query": "What is the bean belt?",
        "relevant_chunks": [44],
    },
    {
        "id": "arabica_elevation",
        "query": "What elevation is ideal for arabica cultivation?",
        "relevant_chunks": [44],
    },

    # ---- Category 2: Paraphrased questions ----
    {
        "id": "caffeine_mechanism",
        "query": "How does caffeine keep people awake?",
        "relevant_chunks": [47],
    },
    {
        "id": "dark_roast_caffeine",
        "query": "Are dark roasts higher in caffeine?",
        "relevant_chunks": [50],
    },
    {
        "id": "premium_regions",
        "query": "What regions are known for premium coffee?",
        "relevant_chunks": [45],
    },

    # ---- Category 3: Conceptual questions ----
    {
        "id": "maillard_reaction_role",
        "query": "What role does the Maillard reaction play in coffee flavor?",
        "relevant_chunks": [46],
    },
    {
        "id": "arabica_vs_robusta_flavor",
        "query": "How does the flavor of arabica compare to robusta?",
        "relevant_chunks": [42, 43],
    },

    # ---- Category 4: Specific factual questions ----
    {
        "id": "arabica_percentage",
        "query": "What percentage of world production is arabica?",
        "relevant_chunks": [42],
    },
    {
        "id": "yemen_arrival",
        "query": "When did coffee cultivation reach Yemen?",
        "relevant_chunks": [43],
    },

    # ---- Category 5: Questions where multiple chunks could be relevant ----
    {
        "id": "coffee_quality_factors",
        "query": "What environmental factors influence coffee bean quality?",
        "relevant_chunks": [44, 45],
    },

    # ---- Category 6: Unanswerable questions ----
    {
        "id": "espresso_machine",
        "query": "What is the best brand of espresso machine?",
        "relevant_chunks": [],
    },
    {
        "id": "cold_brew_recipe",
        "query": "How do you make cold brew coffee?",
        "relevant_chunks": [],
    },
    {
        "id": "pregnancy_caffeine_limit",
        "query": "What is the daily caffeine limit for a pregnant woman?",
        "relevant_chunks": [],
    },
]
