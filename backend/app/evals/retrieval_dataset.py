from typing import TypedDict

class TestCase(TypedDict):
    id: str
    query: str
    relevant_chunks: list[int]
    document_id: int

# document_id reference:
#   4  = sample_coffee_report.pdf   (5 pages, single topic)
#  10  = backend_walkthrough_script.pdf (5 pages, interview-prep script)
#  11  = Rich-Dad-Poor-Dad-2.pdf    (241 pages, real book)

TEST_CASES: list[TestCase] = [
    # ---- Existing 8 cases ----
    {
        "id": "roast_taste",
        "query": "How does roast level affect the taste of coffee?",
        "relevant_chunks": [49],
        "document_id": 4,
    },
    {
        "id": "dark_light_roast",
        "query": "Why do darker and lighter roasted beans taste different?",
        "relevant_chunks": [49],
        "document_id": 4,
    },
    {
        "id": "coffee_caffeine",
        "query": "How much caffeine is in a 240-milliliter cup of coffee?",
        "relevant_chunks": [48],
        "document_id": 4,
    },
    {
        "id": "roasting_chemical_reactions",
        "query": "What chemical reactions occur during coffee roasting?",
        "relevant_chunks": [46],
        "document_id": 4,
    },
    {
        "id": "roasting_bean_changes",
        "query": "What happens to coffee beans during roasting?",
        "relevant_chunks": [46],
        "document_id": 4,
    },
    {
        "id": "coffee_origin",
        "query": "Where did coffee originate?",
        "relevant_chunks": [42],
        "document_id": 4,
    },
    {
        "id": "commercial_species",
        "query": "Which coffee species dominate commercial production?",
        "relevant_chunks": [42],
        "document_id": 4,
    },
    {
        "id": "arabica_cost",
        "query": "Why is Arabica more expensive to cultivate?",
        "relevant_chunks": [43],
        "document_id": 4,
    },

    # ---- Category 1: Direct questions ----
    {
        "id": "discover_coffee",
        "query": "Who discovered coffee according to local legend?",
        "relevant_chunks": [43],
        "document_id": 4,
    },
    {
        "id": "bean_belt",
        "query": "What is the bean belt?",
        "relevant_chunks": [44],
        "document_id": 4,
    },
    {
        "id": "arabica_elevation",
        "query": "What elevation is ideal for arabica cultivation?",
        "relevant_chunks": [44],
        "document_id": 4,
    },

    # ---- Category 2: Paraphrased questions ----
    {
        "id": "caffeine_mechanism",
        "query": "How does caffeine keep people awake?",
        "relevant_chunks": [47],
        "document_id": 4,
    },
    {
        "id": "dark_roast_caffeine",
        "query": "Are dark roasts higher in caffeine?",
        "relevant_chunks": [50],
        "document_id": 4,
    },
    {
        "id": "premium_regions",
        "query": "What regions are known for premium coffee?",
        "relevant_chunks": [45],
        "document_id": 4,
    },

    # ---- Category 3: Conceptual questions ----
    {
        "id": "maillard_reaction_role",
        "query": "What role does the Maillard reaction play in coffee flavor?",
        "relevant_chunks": [46],
        "document_id": 4,
    },
    {
        "id": "arabica_vs_robusta_flavor",
        "query": "How does the flavor of arabica compare to robusta?",
        "relevant_chunks": [42, 43],
        "document_id": 4,
    },

    # ---- Category 4: Specific factual questions ----
    {
        "id": "arabica_percentage",
        "query": "What percentage of world production is arabica?",
        "relevant_chunks": [42],
        "document_id": 4,
    },
    {
        "id": "yemen_arrival",
        "query": "When did coffee cultivation reach Yemen?",
        "relevant_chunks": [43],
        "document_id": 4,
    },

    # ---- Category 5: Questions where multiple chunks could be relevant ----
    {
        "id": "coffee_quality_factors",
        "query": "What environmental factors influence coffee bean quality?",
        "relevant_chunks": [44, 45],
        "document_id": 4,
    },

    # ---- Category 6: Unanswerable questions ----
    {
        "id": "espresso_machine",
        "query": "What is the best brand of espresso machine?",
        "relevant_chunks": [],
        "document_id": 4,
    },
    {
        "id": "cold_brew_recipe",
        "query": "How do you make cold brew coffee?",
        "relevant_chunks": [],
        "document_id": 4,
    },
    {
        "id": "pregnancy_caffeine_limit",
        "query": "What is the daily caffeine limit for a pregnant woman?",
        "relevant_chunks": [],
        "document_id": 4,
    },

    # ---- Category 7: Harder documents — added after finding real failures ----
    # These are not hypothetical. "father_experience" and "library_business"
    # are the exact two questions that failed live, verified against the
    # actual ingested text before being added here (see
    # EVIDENCE_GATE_CALIBRATION.md for the full investigation). The other
    # two are control cases on the same documents that we already confirmed
    # work, so a future regression here is measured against a known-good
    # baseline, not just known-bad ones.
    {
        "id": "server_js_purpose",
        "query": "Tell me what server.js file does",
        "relevant_chunks": [162],
        "document_id": 10,
    },
    {
        "id": "asset_liability_definition",
        "query": "What is the difference between an asset and a liability?",
        "relevant_chunks": [400],
        "document_id": 11,
    },
    {
        "id": "father_experience",
        "query": "tell me the author's experience about the library bussiness",
        "relevant_chunks": [375, 379, 380],
        "document_id": 11,
    },
    {
        "id": "library_business",
        "query": "Tell me about the comic book library",
        "relevant_chunks": [375, 380],
        "document_id": 11,
    },
]
