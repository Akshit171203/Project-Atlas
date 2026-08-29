from typing import TypedDict

class Case(TypedDict):
    name: str
    query: str
    answerable: bool

CASES: list[Case] = [

    {
        "name": "answerable_roast",
        "query": "Why does roast level affect the taste of coffee?",
        "answerable": True,
    },

    {
        "name": "answerable_caffeine",
        "query": "How much caffeine is in a 240-milliliter cup of coffee?",
        "answerable": True,
    },

    {
        "name": "answerable_maillard",
        "query": "What role does the Maillard reaction play in coffee roasting?",
        "answerable": True,
    },

    {
        "name": "unanswerable_computer_virus",
        "query": "What are the symptoms of a computer virus?",
        "answerable": False,
    },

    {
        "name": "unanswerable_stock_market",
        "query": "What caused the stock market to rise today?",
        "answerable": False,
    },

    {
        "name": "unanswerable_python",
        "query": "How do I implement a binary search tree in Python?",
        "answerable": False,
    },

]   