# 8. Open problems

Three known failures, plus the smaller things found while writing these
docs. Each entry says what's wrong, why it's hard, and what would
plausibly fix it — so that picking one up later starts from a diagnosis
rather than from scratch.

---

## 1. `library_business_known_failure` — the reranker is lexically brittle

**Status:** open, root-caused, fix identified.
**Full investigation:** [`EVIDENCE_GATE_CALIBRATION.md`](../backend/EVIDENCE_GATE_CALIBRATION.md),
explained in [doc 2](02-retrieval-failures.md).

The query *"tell me the author's experience about the library bussiness"*
is refused, though the content exists verbatim in chunk 375 (the
comic-book library in Mike's basement).

**Why it's hard.** The same chunk scores about **-10** for that phrasing
and **+3.00** for *"Tell me about the comic book library."* A ~13-point
swing on identical content from word choice alone — and -10 is where
genuinely off-topic queries score. There is no threshold that separates a
relevant chunk at -10 from an irrelevant one at -10.6, because there's
nothing there to separate. `top_k` doesn't help either; the ordering is
already wrong before you sort.

`cross-encoder/ms-marco-MiniLM-L6-v2` is a small distilled model trained
on Bing click data — short keyword-ish queries paired with passages that
share their vocabulary. It behaves much more like a strong fuzzy keyword
matcher than a semantic reasoner.

**Tried:** query rewriting (helped, gated behind initial failure, doesn't
fully fix this case); keyword-search candidate merging (**reverted** —
didn't fix it *and* caused a regression, [doc 2](02-retrieval-failures.md)).

**Most promising next step:** swap the reranker. `RERANKER_MODEL` in
[`config.py`](../backend/app/core/config.py) is a config line; a modern
reranker (BGE-reranker, a larger cross-encoder, or a hosted rerank API) is
trained on more diverse and more conversational data. Then re-run
`evaluate_retrieval.py` — 26 cases, no LLM calls, seconds — and see
whether Recall@1 and MRR move. This is the highest value-per-effort item
in the whole project.

**Second:** HyDE. Have the LLM write a hypothetical passage answering the
question and retrieve with *that* embedding. It attacks the root cause —
you'd be matching document-shaped text against document-shaped text
instead of question-shaped text against document-shaped text.

---

## 2. `server_js_purpose` — sentence-splitting destroys pronoun antecedents

**Status:** open, **newly root-caused while writing these docs** (the
previous explanation was wrong).
**Explained in:** [doc 4](04-hallucination-and-verification.md).

The standing note said this case and `coffee_origins` both failed because
"claims are true but phrased differently from the source, so NLI won't
call them entailed" — paraphrase brittleness. Running the NLI model
directly on the verbatim chunk sentences showed that is **not what's
happening.**

The source chunk (162) reads: *"Back in server.js, this file acts as the
orchestrator. **It** spins up the HTTP server, connects to Redis, binds
Socket.IO to the server, and starts the background cron jobs."*

`citation_verifier.py` tests each sentence separately as an NLI premise:

| Premise | Hypothesis | Label | Entailment |
|---|---|---|---|
| "**It** spins up the HTTP server, connects to Redis…" | "server.js spins up the HTTP server." | `neutral` | **0.001** |
| "**server.js** spins up the HTTP server, connects to Redis…" | "server.js spins up the HTTP server." | `entailment` | **0.998** |

**One word moves entailment from 0.001 to 0.998.** The model is right:
given only *"It spins up the HTTP server,"* there is no way to know what
*It* is.

The bug is ours. Sentence-splitting is what makes NLI accurate (long
premises dilute the signal), but it also severs every **anaphoric
reference** — *it*, *this file*, *the plant*, *they* — whose antecedent
lives in a previous sentence. Good prose is full of these, precisely
because repeating the subject reads badly, so the sentences carrying the
substantive detail are disproportionately the ones starting with a
pronoun.

**Fixes, in order of effort:**

1. **Sliding-window premises.** Test each sentence *and* each adjacent
   pair, keep the best score. Antecedents are almost always in the
   immediately preceding sentence. Roughly doubles local NLI work — which
   is free — and needs no new models. Clearest mechanism, smallest change.
2. **Whole-chunk fallback.** If every sentence returns neutral, retry once
   with the full chunk as premise. Accepts dilution only for claims
   already headed for failure.
3. **Coreference resolution at ingestion.** Rewrite pronouns to their
   antecedents before storing. Most thorough, most machinery, and it would
   improve retrieval too, since chunk embeddings would carry their
   subjects.

Option 1 is the one to try first, and `evaluate_citations.py` should gain
an anaphora case before the change so the fix is measured rather than
assumed.

---

## 3. `coffee_origins` — chunking splits the answer away from its heading

**Status:** open, **root-caused during this documentation pass** (the
previous diagnosis was falsified, then replaced by a measured one).
**Explained in:** [doc 4](04-hallucination-and-verification.md).

Grouped with case 2 under "paraphrase brittleness." NLI is not involved.
The verbatim source sentence tested against a clean paraphrase scores
`entailment` at **0.997** — it would pass easily. The real chain, measured:

**a. The chunk holding the answer is never retrieved.** The sentence *"The
plant is native to the highlands of Ethiopia"* is in **chunk 43**. Vector
search's top 10 for *"Where did coffee originate?"* is
`[53, 42, 51, 54, 44, 60, 45, 55, 65, 46]`. Chunk 43 is absent — and
absent for the rephrasing *"Where did coffee come from originally?"* too.
Both its neighbours (42, 44) are retrieved; the chunk between them, with
the answer, is not. It never reaches the reranker.

**b. Why:** chunk 43 begins *"romatic flavor, while robusta contains
nearly twice the caffeine and grows more easily at lower altitudes..."* —
about half of it is robusta economics, with the Ethiopia sentence buried
in the middle. A single 384-dimension vector averages the whole chunk, and
that average sits far from a question about origins.

**c. The heading won instead.** Chunk 42 reranks **first at +6.523**
because it carries the section heading *"1. The Coffee Plant and Its
Origins."* Its body is cut off at *"while robusta contains nearly"* —
before the Ethiopia sentence. **The heading that advertises the answer and
the text that contains it are in different chunks**, and the reranker
took the heading. Keyword collision (case 1) on the *easy* document.

**d. The model behaved correctly.** Given those five chunks it answered
*"The exact origin of the coffee plant is not specified in the provided
sources"* — which is **true of the sources it was shown.** No
hallucination; it correctly reported a gap that retrieval manufactured.

**e. The claim that actually failed is severed by a chunk boundary.** The
one claim still unsupported after repair —

> *"A French naval officer named Gabriel de Clieu carried a single seedling
> across the Atlantic to the Caribbean island of Martinique in 1723."*

— scores `neutral` at **0.003** against every source, and is nonetheless
entirely present in the document, split in two: **chunk 53** ends
*"...a French naval officer named Gabriel de Clieu carried a single
seedling across the Atlantic to"* and **chunk 54** begins *"carried a
single seedling across the Atlantic to the Caribbean island of Martinique
in 1723..."*. Chunk 53 has the **who**; chunk 54 has the **where and
when**. The LLM combined them correctly. Verification tests each source
separately, and **neither half entails the whole.**

This is a structural limit worth naming: **per-source verification cannot
validate a claim synthesized across sources** — and cross-source synthesis
is exactly what the generator is asked to do. Checking every source rather
than the cited one ([doc 4](04-hallucination-and-verification.md)) doesn't
help, because the evidence isn't in any *single* source.

**f. Repair made it stranger.** It dropped one failing claim, added three
new well-supported ones, and kept the unsupportable one — so the case
fails after a full repair round that cost two extra LLM calls.

### What to fix

Almost all of it is chunking, which is upstream of everything else:

1. **Sentence-aware chunk boundaries.** Never split mid-sentence. Fixes
   (e) by construction, and stops fragments like *"romatic flavor"* and
   *"ivation spread across the Red Sea"* from leading a chunk. This is the
   single highest-leverage change for this case.
2. **Heading propagation.** Prepend the current section heading to each
   chunk's embedded text. Fixes (c) — the answer chunk would carry
   *"The Coffee Plant and Its Origins"* too, and stop losing to a chunk
   that has the heading and nothing else.
3. **Smaller chunks, or semantic chunking.** Addresses (b) — a chunk that
   is half robusta economics and half origin history has no coherent
   average to embed.
4. **Multi-source premises in verification.** For (e) specifically:
   concatenating adjacent retrieved chunks as a premise, or reconstructing
   original sentences across boundaries. Meaningfully more complex than
   1-3, and mostly unnecessary if 1 is done.

**Note that nothing on this list is a better model.** Not a better
reranker, not a better NLI model, not a better prompt. Every one of the
downstream levers this project has reached for is irrelevant to this
case — which is what makes it the most instructive failure of the three.

---

## 4. Summarization queries can't work — architectural, not a bug

**Status:** documented limitation, working as designed.

*"Summarise chapter 1 for me"* is correctly refused (best rerank score
**-3.42**, below the -2.0 gate). It should be.

**Why it's structural.** Retrieval matches a *specific information need*
to *specific passages*. A summarization request has no specific content to
match — it's a request about a **structural region** of a document, and
this system has no concept of structural regions. Chunking is fixed-size
and page-scoped ([doc 1](01-how-rag-works.md)); no chunk *is* chapter 1,
and nothing records which chunks belong to it. Even with perfect
retrieval, five 500-character chunks cannot summarize a chapter — you'd
need all of it.

The `summarize_chapter_known_limitation` eval case exists to keep this
refusal correct, and it has already caught one change that broke it
([doc 7](07-evaluation-methodology.md)).

**What a real fix needs** — a separate code path, not a tweak:

1. **Structure-aware ingestion** — detect chapter/section boundaries at
   parse time and store them, so chunks know which region they belong to.
2. **Intent classification** — route "summarize X" away from
   retrieve-top-5 to a different pipeline.
3. **Hierarchical summarization** — map-reduce over a region's chunks:
   summarize each, then summarize the summaries. Costs a number of LLM
   calls proportional to document size, not a fixed 5.
4. **A different verification story.** Claim-level NLI against 5 chunks
   doesn't transfer to a summary synthesized from 200.

Point 4 is the one that makes this a genuinely large piece of work rather
than a medium one.

---

## 5. Smaller things worth knowing

**Chunks start mid-word.** This one turned out to matter more than it
looks. [`chunking.py`](../backend/app/services/chunking.py) backs the
chunk *end* off to a whitespace boundary, but advances `start` by a flat
`chunk_size - overlap` with no such adjustment. So a chunk's opening
characters are routinely a word fragment. Real examples from the local
database:

| Chunk | Begins with | Should be |
|---|---|---|
| 43 | `"romatic flavor, while robusta..."` | "aromatic" |
| 44 | `"ivation spread across the Red Sea..."` | "cultivation" |
| 163 | `"n jobs."` | "cron jobs" |

It looks cosmetic. It isn't: that fragment is embedded as part of the
chunk's vector, and it becomes the opening of the first NLI premise built
from that chunk. Chunk 43 is the chunk that holds the `coffee_origins`
answer and never gets retrieved (#3).

The `start` fix is three lines. The **bigger** version of the same problem
— splitting mid-*sentence*, which severs facts across chunks and produces
subject-less premises — is what actually breaks #3(e), and needs
sentence-aware boundaries rather than a whitespace nudge.

**`HybridRetriever` is fully implemented and unwired.**
[`hybrid_retrieval.py`](../backend/app/services/hybrid_retrieval.py) plus
Reciprocal Rank Fusion in
[`rank_fusion.py`](../backend/app/services/rank_fusion.py) work and are
unused by the main pipeline, for the measured reasons in
[doc 2](02-retrieval-failures.md). Kept rather than deleted: it's the
right tool for a corpus where exact-term matching matters (error codes,
product names, proper nouns), and the reason it lost here is specific to
this corpus and this reranker.

**No shared contract between backend and frontend types.** Pydantic models
and the hand-written TypeScript interfaces in
[`api.ts`](../frontend/src/lib/api.ts) are two independent sources of
truth. Nothing enforces they stay in sync — when `RAGResult` gained
`metrics` and `rejected`, the TS types were updated by hand. The scale
answer is OpenAPI codegen (`openapi-typescript`) against FastAPI's
generated schema. See
[`INTEGRATION_NOTES.md`](../frontend/INTEGRATION_NOTES.md).

**No streaming.** `/query` blocks for 73-80s and returns everything at
once. Streaming the generation call's tokens would make the wait feel
dramatically shorter, but the pipeline can't stream a *final* answer — the
answer isn't trustworthy until verification and repair have run, and those
need the complete text. A more honest UX would stream pipeline *stages*
("retrieving… generating… verifying 6 claims…") over SSE rather than
tokens. The frontend already shows an elapsed-time indicator as a
stopgap.

**No auth, no multi-tenancy, no rate limiting.** Every document is visible
to everyone; `/documents` returns all of them. Fine for a local
single-user tool, and the first thing to fix before this is exposed
anywhere.

**The evidence-gate threshold is calibrated on a handful of examples.**
`-2.0` sits in an observed gap between two small clusters, not on a
labeled dataset ([doc 3](03-evidence-gate.md)).

---

## If you're picking this up again

Current state: **8/11 end-to-end**, repair rate **0.455**. The three
failures are #1, #2 and #3 above.

Rough value-per-effort order:

1. **Sentence-aware chunking + heading propagation.** Fixes most of #3,
   removes the mid-word fragments, and is upstream of retrieval *and*
   verification — the only item on this list that improves both halves of
   the pipeline. Requires re-ingesting documents, which renumbers chunks
   and invalidates the retrieval suite's hand-labeled ground truth
   ([doc 7](07-evaluation-methodology.md)) — budget for relabeling.
2. **Swap the reranker and re-run `evaluate_retrieval.py`.** One config
   line, a deterministic suite that runs in seconds, aimed at the deepest
   problem in the system (#1).
3. **Sliding-window NLI premises.** Small, well-understood, with a
   measured 0.001 → 0.998 result waiting for it (#2). Add an anaphora case
   to `evaluate_citations.py` first so the fix is measured, not assumed.
4. **Fix mid-word chunk starts** (#5). Three lines, if you aren't doing 1.
5. **Merge claim extraction into generation** — removes a whole LLM call,
   the largest available latency win, but needs a real quality comparison
   first ([doc 6](06-cost-and-latency.md)).

Whatever you pick: **run `evaluate_rag.py` before and after.** Two
reasonable-looking changes in this project's history made things worse
(5/7 → 4/7, and 8/11 → 7/11), and both were caught only because the number
moved the wrong way.

---

**Back to:** [README](README.md)
