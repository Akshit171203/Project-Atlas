# Evidence gate threshold calibration

How a real user-reported bug ("why isn't it considering these questions?")
led to finding and fixing a genuine miscalibration in the evidence gate,
and a second, related retrieval-quality issue it exposed along the way.

## The report

Testing the frontend against a real 241-page book (`Rich-Dad-Poor-Dad-2.pdf`,
not one of the earlier sample documents), two questions came back as
`"I don't have enough information in the knowledge base to answer this
question."` with `0 LLM calls` — meaning the evidence gate
([`app/services/evidence_gate.py`](app/services/evidence_gate.py)) rejected
them before generation ever ran:

1. *"summarise chapter 1 for me"*
2. *"what does author's father does?"*

A third question, *"who's the author of this book?"*, worked fine.

## First question: is this the known vague-query limitation?

Earlier in this project, we established that summarization-style queries
(*"tell me about this document"*) legitimately fail: chunk-retrieval RAG
matches specific information needs to specific passages, and a query with
no specific content has nothing to match well against. Query 1 above is
exactly that pattern — expected to fail, not a bug.

Query 2 is different. *"Rich Dad Poor Dad"* is a book literally structured
around the author's two father figures — this is core, heavily-covered
content, not an edge case. A specific question about well-covered content
being refused is worth investigating, not writing off as the same known
limitation.

## Root cause: the rerank threshold, not phrasing

[`EvidenceGate.is_answerable()`](app/services/evidence_gate.py) rejects a
query if the best `rerank_score` among retrieved chunks is below
`min_rerank_score` (previously `0.0`). Checked actual scores directly
(bypassing the LLM, querying `RerankedRetriever` in isolation) across four
query types on real data:

| Query | Best rerank score | Should be answerable? |
|---|---|---|
| "who's the author of this book?" | **1.39** | yes — worked |
| "what does author's father does?" | **-0.33** | yes — was wrongly rejected |
| "summarise chapter 1 for me" | **-3.42** | no — correctly rejected either way |
| Off-topic negative controls (from the eval suite, different document) | **-10.6 to -11.3** | no |

`cross-encoder/ms-marco-MiniLM-L6-v2` scores are not centered at zero —
genuinely relevant matches on this data measured as low as -0.33, while
truly irrelevant queries scored below -10. A threshold of `0.0` was
rejecting real, well-supported questions along with the vague ones,
because it sat inside the range of scores a *good* match can produce, not
at the boundary between good and bad matches.

**Fix:** `min_rerank_score` changed from `0.0` to `-2.0` — chosen to sit
in the clear gap between the "relevant" cluster (-0.33 to 1.4) and the
"no real match" cluster (-3.4 and below), with a comfortable margin on
both sides. Re-ran the existing 7-case eval suite (which includes 2
off-topic negative controls) after the change — both still correctly
refused. This is calibration from a handful of real examples across two
documents, not a rigorous statistical threshold — worth revisiting with a
larger, deliberately-labeled answerable/unanswerable dataset if this
system needs to scale past ad-hoc testing.

## Second, deeper issue this uncovered

Fixing the threshold let query 2 through the gate — but the model then
said *"the sources do not mention what the author's father does."* Wrong
gate, right refusal reason this time? Checked what actually got retrieved:
the top-3 chunks were all "About the Author" biography content (about
Robert Kiyosaki himself), not the "two dads" content the book is famous
for.

**Why:** the reranker keys heavily on lexical overlap. The query contains
the word *"author"* — which strongly matches the biography section — and
outranks chunks discussing *"father"/"dad"* content, even though those are
what the question is actually asking about. This is a keyword-collision
failure mode: the query happens to share a strong keyword with irrelevant
content and a weaker semantic connection to the relevant content.

Confirmed the relevant chunks (discussing "two fathers," "each dad's
advice") *do* exist in the retrieval candidate pool — just ranked 4th-5th,
below the `top_k` cutoff that was in place at the time of testing
(`top_k=3`, from [`COST_OPTIMIZATION.md`](COST_OPTIMIZATION.md)). Also
tested whether swapping to the already-built `HybridRetriever`
(vector+keyword fusion, currently unused by the main pipeline — see
`app/services/hybrid_retrieval.py`) would fix this on its own: it does
pull the right chunks into the candidate pool, but reranking is
retrieval-source-agnostic — a chunk's rerank score doesn't depend on
whether vector or keyword search found it, so the same 3 biography chunks
still win at `top_k=3` regardless of retrieval strategy. The actual fix
was raising `top_k` back to 5, giving the LLM enough context for the
correctly-relevant-but-imperfectly-ranked chunks to be included at all —
see `app/services/rag.py`.

## The trade-off this reopens

Raising `top_k` back to 5 gives back some of the token/latency savings
from `COST_OPTIMIZATION.md` — that document's numbers were measured at
`top_k=3` and are no longer the current configuration. This is a genuine,
acknowledged tension: `top_k=3` measurably reduced cost and (on the
7-case coffee-report eval set) *improved* the success rate, but it also
measurably broke a real, specific, well-supported question on a different,
more complex document. Optimizing purely for one document's eval numbers
without testing recall on a harder document would have shipped a
regression. `top_k=5` is the current setting; `HybridRetriever` remains
unwired into the main pipeline and is a reasonable next thing to actually
adopt, since it improves recall in cases where vector search alone
wouldn't surface a candidate at all (not just cases where it under-ranks
one) — untested territory for now.

## What happened after both fixes landed

With `min_rerank_score=-2.0` and `top_k=5`, re-querying *"what does
author's father does?"* on the same book: retrieval now correctly
includes the "Rich Dad's Advice" chunk, and the model generated a
genuinely grounded, correctly-cited answer from it (citation verification:
5 of 6 claims supported). But the pipeline still declined to serve it —
this time the relevance evaluator caught it, not citation verification:
*"The answer does not address what the author's father does, but rather
quotes Rich Dad's advice."*

That's actually correct behavior, not a remaining bug: the retrieved
content covers the father's *advice and philosophy*, not his literal
*occupation* — a subtle but real distinction the relevance check is
designed to catch (see the prompt-injection work earlier in this
project's history, where the same relevance gate was the only layer that
caught a hijacked answer). The evidence gate and retrieval fixes did their
job — getting the right content in front of the model — and a separate,
independent safety layer correctly identified that "grounded and cited"
still isn't the same as "actually answers what was asked." Both are
supposed to be true before an answer is served, and here only one was.
