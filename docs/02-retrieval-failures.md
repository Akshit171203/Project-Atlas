# 2. Where retrieval breaks

> Prerequisite: [doc 1](01-how-rag-works.md), specifically the bi-encoder
> vs cross-encoder section.

Retrieval sets the ceiling. If the passage that answers the question isn't
in the five chunks handed to the LLM, no prompt, no model upgrade and no
verification layer can produce a correct grounded answer. Every failure in
this document is a failure to *find* something that was there the whole
time.

The full investigation transcripts, with the actual measured scores, live
in [`EVIDENCE_GATE_CALIBRATION.md`](../backend/EVIDENCE_GATE_CALIBRATION.md).
This document explains the mechanisms behind them.

---

## Problem 1: keyword collision — the reranker matched the wrong "author"

### The symptom

Against *Rich Dad Poor Dad* — a book whose entire premise is the contrast
between the author's two father figures — the question **"what does
author's father does?"** came back with *"the sources do not mention what
the author's father does."*

That content is not obscure in that book. It's the book.

### What was actually retrieved

The top three chunks were all **"About the Author"** biography material —
publisher-page content about Robert Kiyosaki. Not one of them was the
"two dads" content.

### Why

The query contains the word **"author."** The biography section contains
the word "author" many times. The chunks that actually answer the question
talk about *"my rich dad," "my poor dad," "my father"* — and almost never
use the word "author," because a book doesn't refer to its own writer that
way in the narrative.

The reranker scored on the overlap it could see. A strong lexical match
against irrelevant content beat a weaker lexical match against exactly the
right content.

**The concept:** this is a *keyword collision*. The query shares a
high-signal term with the wrong part of the corpus, and shares only a
semantic relationship — no shared vocabulary — with the right part. It is
the specific failure mode you'd expect keyword search to have. Finding it
in a neural reranker is the surprise, and it's the thread that leads to
problem 3.

### The fix, and what it doesn't fix

The correct chunks *were* in the candidate pool, ranked 4th and 5th — just
below the `top_k=3` cutoff in place at the time. Raising `top_k` back to
**5** let them through.

That is a mitigation, not a cure. It buys two slots of margin against
misranking. It does nothing if the right chunk ranks 7th, and nothing at
all for problem 3 below. It also gives back some of the token savings
measured in [`COST_OPTIMIZATION.md`](../backend/COST_OPTIMIZATION.md) —
those numbers were taken at `top_k=3` and no longer describe the live
config. That trade is recorded in a comment right at the call site in
[`rag.py`](../backend/app/services/rag.py).

---

## Problem 2: vector search missed the chunk entirely

### The symptom

**"tell me the author's experience about the library bussiness"** →
refused as unanswerable.

An earlier pass concluded the content simply wasn't in the book. That
conclusion was reached by looking at rerank scores, seeing them deeply
negative, and inferring "no match."

**It was wrong.** Grepping the actual ingested chunk text — bypassing
retrieval and scores entirely — found chunk 375, verbatim:

> *"Using a spare room in Mike's basement, we began piling hundreds of
> comic books in that room. Soon our comic-book library was open to the
> public. We hired Mike's younger sister... to be head librarian. She
> charged each child 10 cents admission..."*

**The methodological lesson is the durable one here:** a low retrieval
score is evidence about *retrieval*, never evidence about *the corpus*.
Concluding "the document doesn't contain X" from "the retriever didn't
find X" assumes the retriever works — which is precisely the thing under
investigation. When you need to know whether content exists, read the
stored text.

### Why it wasn't retrieved

Chunk 375 ranked **12th** by cosine similarity — outside the
`candidate_k=10` window the pipeline pulls before reranking runs. The
reranker never scored it, because the reranker only ever sees what the
bi-encoder hands it.

The vocabulary explains it. The question says *"library business,"
"experience," "author."* The passage says *"comic books," "basement,"
"head librarian," "10 cents admission."* Semantically these are the same
event. Lexically they share one word — *library* — and the
384-dimensional summary of a narrative passage about kids in a basement
doesn't sit especially close to an abstract query about business
experience.

This is the bi-encoder ceiling from doc 1, showing up in a real case:
vector-only Recall@3 and Recall@5 are both 0.826 precisely because when
this model misses, it misses completely.

---

## Problem 3: the reranker is lexically brittle

This is the deepest issue in the retrieval stack, and it undermines the
assumption both earlier fixes rest on.

### The measurement

Same document, same underlying question, two phrasings:

| Phrasing | chunk 375's rerank score |
|---|---|
| "tell me the author's experience about the library bussiness" | ~ **-10** (not in top 5) |
| "Tell me about the comic book library" | **+3.00** |

**A ~13-point swing on identical content from word choice alone.**

For calibration, off-topic negative controls — questions about a
completely different document — score between -10.6 and -11.3. So the
paraphrased-but-correct chunk scored *about as badly as content that has
nothing to do with the question.*

### Why this happens

`cross-encoder/ms-marco-MiniLM-L6-v2` is trained on **MS MARCO**: real Bing
search queries paired with passages people clicked. Two things follow.

1. **Its training distribution is search queries** — short, keyword-ish
   ("coffee origin ethiopia"), not conversational questions with
   possessive constructions and typos.
2. **Its supervision signal is relevance-as-judged-by-clicks**, and
   clicked results overwhelmingly share vocabulary with the query. The
   model was never strongly rewarded for bridging a paraphrase gap,
   because in its training data that gap mostly wasn't there.

Add that it's a **MiniLM** — a distilled 6-layer model chosen for speed —
and you get something that behaves like a very good fuzzy keyword matcher
with some semantic ability layered on, rather than a deep semantic
reasoner. That's an entirely reasonable engineering trade for a reranker
that has to run on every query. It's just not what "neural semantic
reranker" makes you expect.

### Why it breaks the earlier fixes' assumptions

Both problem 1's fix (`top_k=5`) and the evidence gate's threshold
calibration ([doc 3](03-evidence-gate.md)) assume **the rerank score is a
trustworthy relevance signal that just needs the right cutoff and enough
slots.** Problem 3 says the signal itself can be wrong — a genuinely
relevant passage can score like off-topic noise. No value of `top_k` and
no threshold fixes that, because the ordering it would need to fix is
already wrong before you sort.

### The fix that shipped: query rewriting, gated behind failure

If the reranker is sensitive to phrasing, change the phrasing. An LLM
rewrites the question into language a document would plausibly use —
[`query_rewrite.py`](../backend/app/prompts/query_rewrite.py) explicitly
instructs it to replace abstract framing like *"the author's experience
with X"* with concrete narrative wording, and to fix typos.

Retrieval then runs for both phrasings, and
[`reranked_retrieval.py`](../backend/app/services/reranked_retrieval.py)
keeps **each chunk's best score across phrasings** — a chunk survives if
it matches *any* wording of the same question. That's the direct
countermeasure to a 13-point phrasing swing.

**The important part is the gating.** Query rewriting runs *only if the
original phrasing already failed the evidence gate*:

```python
if not self.evidence_gate.is_answerable(chunks):
    rewritten_query = await query_rewriter.rewrite(query)
    ...
```

The first attempt applied it unconditionally, to every query. **The eval
suite went 5/7 → 4/7.** Rewriting a question that was already working
pulled in the rewrite's candidates and let them displace better ones from
the original phrasing — a rewrite is a *different* question, and a
different question retrieves different chunks.

Gated behind an initial failure, the transformation becomes **strictly
additive**: it can only run on queries that already produced nothing, so
the worst case is "still nothing." It cannot break a working query,
because it never touches one. It also costs zero extra LLM calls on the
happy path.

> **The general principle, and it recurs:** an intervention that improves
> the cases you're studying can degrade the cases you aren't. Applying it
> only where the system has already demonstrably failed converts a risky
> change into a safe one. This is a fallback, not a pipeline stage.

---

## Tried and reverted: merging keyword search into the candidate pool

**The hypothesis was good.** Problem 2 showed vector search missing a
chunk outright. Keyword search finds chunk 375 at rank 8 via exact term
overlap on "library" — the machinery already existed
([`keyword_retrieval.py`](../backend/app/services/keyword_retrieval.py),
Postgres full-text search, plus
[`rank_fusion.py`](../backend/app/services/rank_fusion.py) implementing
Reciprocal Rank Fusion). So: pull candidates from vector *and* keyword
search, widening what's eligible for reranking without changing how
ranking works. This is textbook hybrid retrieval.

**It was reverted. It failed twice over.**

### It didn't fix the case it was built for

Chunk 375 entered the candidate pool — and still didn't make the final
top 5.

**Reranking is retrieval-source-agnostic.** A chunk's rerank score is a
function of the `(query, chunk_text)` pair and *nothing else*. It does not
know, and cannot know, which search mode surfaced it. Chunk 375 scores
around -10 for that phrasing whether it arrived via vector search, keyword
search, or was handed over by name.

The bottleneck was never pool composition. It was problem 3 — the
reranker's absolute score for that phrasing. Widening the funnel doesn't
help when the blockage is downstream of the funnel.

### It caused a real regression

For **"summarise chapter 1 for me"** — a query that correctly refused
before — keyword search matched **chunk 230**, which is a page header:
`"Chapter One: Lesson 1"` followed by unrelated narrative. Pure lexical
overlap on *chapter* and *1*. Zero semantic relevance.

Then the lexically-sensitive reranker scored that header chunk **+0.503**
— comfortably above the -2.0 evidence gate — and the system began
answering a question it had been correctly refusing.

**Eval suite: 8/11 → 7/11.** Reverted.

### The lesson worth keeping

**Vector search's semantic nature was silently acting as a filter against
exactly this class of false positive.** A bi-encoder knows a bare heading
carries almost no meaning, so it embeds far from a real content query.
Keyword search has no concept of "this text is structural, not
substantive" — a header containing the query's words is a perfect match by
its measure. And the reranker was too lexically brittle to catch the
difference downstream.

Generalized: **recall is not free.** Every technique that widens what can
be retrieved also widens what can be retrieved *wrongly*, and the gates
downstream are only as good as the candidates they're handed. In a system
whose main promise is "refuses when it should," a false positive is worse
than a miss.

### The second time the same pattern bit

Note this is the **second** unconditional-widening technique to regress
working queries in this project — query rewriting first, keyword merging
second. Query rewriting survived by being gated behind an initial failure.

Keyword merging couldn't be rescued the same way, and it's worth
understanding why: **the regression case is itself an initial-failure
case.** `"summarise chapter 1"` fails the evidence gate on the original
query — that's the correct behavior being protected. A
run-it-only-after-failure gate would have run it there too, and let the
header chunk through anyway. The gate that saved query rewriting is
structurally unable to save this.

**`HybridRetriever` still exists** in
[`hybrid_retrieval.py`](../backend/app/services/hybrid_retrieval.py),
fully implemented and unwired from the main pipeline. Kept rather than
deleted: it's the right tool for a corpus where exact-term matching
matters (product codes, error strings, proper nouns), and the reason it
lost here is specific to this corpus and this reranker.

---

## What would actually fix problem 3

Not implemented — these are real next steps, in rough order of
effort-to-payoff:

- **A better reranker.** `ms-marco-MiniLM-L6-v2` is a small distilled model
  from an older generation. A modern reranker (BGE, Cohere Rerank, a
  larger cross-encoder) is trained on more diverse, more conversational
  data and is materially less phrase-sensitive. This is the highest-value
  single change available, and it's a config line —
  `RERANKER_MODEL` in [`config.py`](../backend/app/core/config.py) — plus
  re-running the 26-case retrieval suite to prove it.
- **Multi-query retrieval as the default.** Generate 3-5 paraphrases up
  front, retrieve for all, take each chunk's best score. The machinery
  already exists (`query_variants` in `RerankedRetriever`); the reason
  it's gated rather than default is the measured 5/7 → 4/7 regression
  above, which a best-score-across-variants merge might survive better
  than the original displacement-based one did. Would need to be measured,
  not assumed.
- **HyDE** (Hypothetical Document Embeddings). Ask the LLM to *write* a
  fake passage answering the question, then retrieve using that passage's
  embedding instead of the question's. It attacks the root cause directly:
  you're now matching document-shaped text against document-shaped text,
  instead of question-shaped text against document-shaped text.
- **Better chunking.** Attaching section headings to each chunk's embedded
  text would give both models structural context they currently lack, and
  would make the chunk-230 header problem structurally impossible.

---

**Next:** [3. The evidence gate](03-evidence-gate.md)
