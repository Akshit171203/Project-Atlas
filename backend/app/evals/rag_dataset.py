# document_id reference:
#   4  = sample_coffee_report.pdf   (5 pages, single topic)
#  10  = backend_walkthrough_script.pdf (5 pages, interview-prep script)
#  11  = Rich-Dad-Poor-Dad-2.pdf    (241 pages, real book)

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
        "document_id": 4,
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
        "document_id": 4,
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
        "document_id": 4,
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
        "document_id": 4,
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
        "document_id": 4,
    },

    {
        "name": "computer_virus",
        "query": (
            "What are the symptoms of a computer virus?"
        ),
        "expected_answer": None,
        "answerable": False,
        "document_id": 4,
    },

    {
        "name": "python_bst",
        "query": (
            "How do I implement a binary search tree in Python?"
        ),
        "expected_answer": None,
        "answerable": False,
        "document_id": 4,
    },

    # ---- Harder documents — added after finding real failures live ----
    # Same reasoning as retrieval_dataset.py: these aren't hypothetical
    # cases, they're the exact questions that failed in real testing this
    # session, added so the eval suite can actually see the bug instead of
    # only testing the one document where retrieval happens to work well.
    # See EVIDENCE_GATE_CALIBRATION.md for the full investigation.

    {
        "name": "server_js_purpose",
        "query": "Tell me what server.js file does",
        "expected_answer": (
            "server.js acts as the orchestrator: it spins up the "
            "HTTP server, connects to Redis, binds Socket.IO, starts "
            "the background cron jobs, and implements graceful "
            "shutdown on SIGTERM."
        ),
        "answerable": True,
        "document_id": 10,
    },

    {
        "name": "asset_liability_definition",
        "query": "What is the difference between an asset and a liability?",
        "expected_answer": (
            "An asset puts money in your pocket; a liability "
            "takes money out of your pocket."
        ),
        "answerable": True,
        "document_id": 11,
    },

    {
        "name": "library_business_known_failure",
        "query": "tell me the author's experience about the library bussiness",
        "expected_answer": (
            "Mike and the author started a comic-book library in "
            "Mike's basement, hiring his sister as head librarian "
            "and charging 10 cents admission."
        ),
        # This is genuinely answerable — the content exists (chunk 375)
        # — but as of this eval set being written, the system says
        # "not answerable" due to the reranker's lexical-brittleness
        # issue documented in EVIDENCE_GATE_CALIBRATION.md. Left as
        # answerable=True (the true expected behavior) specifically so
        # this case FAILS until the underlying bug is actually fixed,
        # rather than quietly redefining "success" to match current
        # broken behavior.
        "answerable": True,
        "document_id": 11,
    },

    {
        "name": "summarize_chapter_known_limitation",
        "query": "summarise chapter 1 for me",
        "expected_answer": None,
        # Unlike the case above, this one SHOULD fail — it's the
        # documented summarization-style limitation (no specific content
        # for retrieval to match against), not a bug. Kept in the suite
        # as a regression guard: if this ever starts returning
        # answerable=True, something changed in the evidence gate that
        # deserves a second look, not celebration.
        "answerable": False,
        "document_id": 11,
    },

]
