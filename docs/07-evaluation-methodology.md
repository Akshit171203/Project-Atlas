# 7. How this is evaluated, and why that mattered more than any single fix

> Code: [`app/evals/`](../backend/app/evals/),
> [`scripts/evaluate_*.py`](../backend/scripts/)

## Why an eval suite exists at all

RAG systems are **non-deterministic and locally convincing**. Change a
threshold, ask your favourite question, get a good answer, ship it. The
question you didn't ask just broke.

That is not hypothetical here. **Two separate "improvements" in this
project regressed working cases, and both were caught only because the
eval ran:**

| Change | Intent | Measured result |
|---|---|---|
| Query rewriting on every query | Fix phrasing brittleness | **5/7 → 4/7** |
| Merging keyword-search candidates | Fix vector-search misses | **8/11 → 7/11** |

Both were reasonable. Both were textbook techniques. Both made the system
worse, and neither would have been visible from spot-checking the query
they were built to fix — because that query *did* improve. The damage was
somewhere else.

**A change is not an improvement until something measured says so.** An
eval suite is what converts "this feels better" into a number that can
disagree with you.

## Four suites, deliberately at different layers

| Script | Measures | LLM calls | Runtime |
|---|---|---|---|
| [`evaluate_retrieval.py`](../backend/scripts/evaluate_retrieval.py) | Recall@k, MRR — 26 cases | none | seconds |
| [`evaluate_citations.py`](../backend/scripts/evaluate_citations.py) | NLI labels on known pairs | none | seconds |
| [`evaluate_answerability.py`](../backend/scripts/evaluate_answerability.py) | Evidence-gate accuracy | none | seconds |
| [`evaluate_rag.py`](../backend/scripts/evaluate_rag.py) | End-to-end success — 11 cases | ~5 per case | **~15 min** |

The layering is the point, and it's the same instinct as a unit/integration
test split.

**When the end-to-end suite drops, it tells you *that* something broke, not
*what*.** A case can fail because retrieval missed, because the gate
mis-thresholded, because NLI rejected a fine claim, or because the
relevance judge was in a mood. One number, five candidate causes.

The component suites isolate those. Retrieval evaluation needs no LLM at
all — it compares retrieved chunk IDs against hand-labeled ground truth —
so it runs in seconds and is **deterministic**, which makes it the tool you
reach for when tuning retrieval. The citation suite pins NLI behaviour on
four fixed pairs covering entailment, neutral, contradiction, and a
wrong-citation case.

Practically: **iterate on the fast deterministic suites, confirm on the
slow end-to-end one.** A 15-minute feedback loop is one you stop running;
a 10-second one is a loop you actually use.

## Retrieval metrics, and reading them properly

From the current run of the 26-case suite:

| Metric | Vector only | Vector + reranker |
|---|---|---|
| Recall@1 | 0.435 | **0.826** |
| Recall@3 | 0.826 | **1.000** |
| Recall@5 | 0.826 | **1.000** |
| MRR | 0.636 | **0.906** |

- **Recall@k** — in what fraction of queries does a relevant chunk appear
  in the top k? *Did we find it at all?*
- **MRR** — mean of 1/(rank of first relevant result). Rank 1 → 1.0,
  rank 2 → 0.5, rank 5 → 0.2. *How high up did we find it?*

Both matter for different reasons. **Recall@5 is the hard constraint** —
`top_k=5` is what the LLM sees, so a chunk outside the top 5 does not
exist as far as answering is concerned. **MRR is about answer quality
within that** — a correct chunk at rank 5, surrounded by four irrelevant
ones, is four chances for the model to draw an unsupported claim from
something adjacent and wrong.

The reading that matters most: **vector-only Recall@3 and Recall@5 are
identical at 0.826.** The line is flat. In the ~17% of queries where the
bi-encoder fails, widening from 3 to 5 recovers nothing, because the right
chunk isn't at rank 4 or 5 — it's outside the top 10 entirely. Reranking
takes @3 and @5 to a perfect 1.000, but only by reordering what it was
handed; it cannot conjure a chunk the first stage never retrieved. That
single flat line is the empirical case for everything in
[doc 2](02-retrieval-failures.md).

## The end-to-end suite, and what "success" means

[`rag_evaluation.py`](../backend/app/evals/rag_evaluation.py) defines
success in a way worth reading closely:

```python
if expected_answerable != actual_answerable:
    final_success = False          # wrong call on answerability
elif not expected_answerable:
    final_success = True           # correct refusal IS success
else:
    final_success = (citations_supported is True
                     and answer_relevant is True)
```

Three things are encoded there.

**1. Correct refusal counts as success.** The suite includes off-topic
controls — `computer_virus` and `python_bst` against a coffee report — and
refusing them is a *pass*. A metric that only rewards answering would push
every change toward answering more, which is precisely the failure mode
this system is built to avoid.

**2. An answer must clear both remaining gates.** Grounded but off-topic
fails. On-topic but unsupported fails. This mirrors the pipeline exactly:
the eval's definition of success and the system's definition of a
servable answer are the same definition, so the metric can't drift from
what the system promises.

**3. `repair_rate` is tracked separately from success.** A repaired answer
still counts as a success — it ended up correct. But a rising repair rate
means generation is degrading even when the final numbers hold, and it
costs two extra LLM calls per occurrence. It's a leading indicator that
success rate alone would hide.

## The discipline that makes the dataset honest

The dataset in [`rag_dataset.py`](../backend/app/evals/rag_dataset.py)
does two things that are easy to skip and hard to recover from later.

### Known bugs are kept as *failing* cases

```python
{
    "name": "library_business_known_failure",
    "query": "tell me the author's experience about the library bussiness",
    "answerable": True,   # ← the TRUE expected behavior
    ...
}
```

The content exists (chunk 375, quoted verbatim in
[doc 2](02-retrieval-failures.md)). The system currently refuses it. The
case is labeled `answerable=True` **specifically so it keeps failing.**

The tempting alternative — relabel it `answerable=False`, watch the suite
go green — redefines correctness as "whatever the system currently does."
Do that a few times and the suite stops measuring the system and starts
describing it. **A suite that always passes has stopped being an
experiment.** The typo in the query is preserved for the same reason: it's
the real question a real user typed, and typo-robustness is part of what's
being tested.

Note the query also keeps its typo (*"bussiness"*) deliberately — real
users type like that, and query rewriting is explicitly instructed to fix
typos.

### Correct limitations are kept as *passing* cases

```python
{
    "name": "summarize_chapter_known_limitation",
    "query": "summarise chapter 1 for me",
    "answerable": False,   # correctly refusing this is a PASS
}
```

The mirror image: this one *should* fail to answer, and the case exists as
a **regression guard**. The comment in the dataset says it directly — if
this ever starts returning `answerable=True`, something changed in the
evidence gate that deserves scrutiny, not celebration.

That guard earned its place. The keyword-merge experiment
([doc 2](02-retrieval-failures.md)) made exactly this query start
answering, off a page-header chunk scoring +0.503. Without a case
asserting that refusing is correct, that regression reads as an
improvement — the system answering *more* questions.

### Failures found in the wild get added to the suite

The last four cases in the dataset carry a comment saying so plainly:
these aren't hypothetical, they're the exact questions that failed during
real testing. Three of them target harder documents — a 241-page book and
a technical script — precisely because the original 7 cases all came from
one clean 5-page coffee report where retrieval happens to work well.

**An eval set drawn from one easy document measures how well the system
handles that document.** `top_k=3` looked like a clear win against the
coffee set and broke a real question on the book. The fix isn't a better
threshold; it's a harder eval set. Every bug found by hand becomes a case,
so it can only ever be found by hand once.

## The current numbers

From a full run of `evaluate_rag.py` (ollama / `llama3.1`, ~15 min):

```
Cases: 11
Successful: 8/11
Success rate: 0.727
Repair rate: 0.455
```

Per case:

| Case | Expected | Answerable | Relevant | Citations | Repaired | Pass |
|---|---|---|---|---|---|---|
| `roast_taste` | answerable | ✅ | ✅ | ✅ | yes | ✅ |
| `coffee_caffeine` | answerable | ✅ | ✅ | ✅ | no | ✅ |
| `maillard` | answerable | ✅ | ✅ | ✅ | yes | ✅ |
| `arabica_robusta` | answerable | ✅ | ✅ | ✅ | yes | ✅ |
| `coffee_origins` | answerable | ✅ | ✅ | ❌ | yes | ❌ |
| `computer_virus` | refuse | ✅ refused | — | — | no | ✅ |
| `python_bst` | refuse | ✅ refused | — | — | no | ✅ |
| `server_js_purpose` | answerable | ✅ | ✅ | ❌ | yes | ❌ |
| `asset_liability_definition` | answerable | ✅ | ✅ | ✅ | no | ✅ |
| `library_business_known_failure` | answerable | ❌ refused | — | — | no | ❌ |
| `summarize_chapter_known_limitation` | refuse | ✅ refused | — | — | no | ✅ |

The three failures split cleanly by **which gate** stopped them, which is
the diagnostic value of recording the columns rather than just the total:

- `library_business_known_failure` never got past the **evidence gate** —
  a retrieval problem ([doc 2](02-retrieval-failures.md)).
- `coffee_origins` and `server_js_purpose` both produced **relevant**
  answers that failed **citation verification** even after repair — and,
  as it turns out, for two completely unrelated reasons
  ([doc 4](04-hallucination-and-verification.md)).

Note also that `arabica_robusta` — a persistent failure in the earlier
7-case runs recorded in
[`COST_OPTIMIZATION.md`](../backend/COST_OPTIMIZATION.md) — now passes.

**Repair rate 0.455** means 5 of 11 queries needed a repair round: two
extra LLM calls each. Three of those five went on to pass, which is repair
doing its job. Two didn't, and paid the cost anyway.

## Where this methodology is still thin

Named honestly:

- **11 end-to-end cases across 3 documents is small.** Enough to catch
  gross regressions (it caught two), not enough for confidence in a
  one-case change — 8/11 vs 9/11 is a single query.
- **Non-determinism isn't quantified.** Local LLMs vary run to run, and the
  suite runs once. A case flipping might be a regression or might be
  noise, and nothing here distinguishes them. Repeated runs with
  variance reported would.
- **No answer-quality metric beyond the gates.** Success means "grounded
  and relevant." Whether the answer is *good* — complete, well-organized,
  the best available from those chunks — isn't measured at all.
- **The evidence-gate threshold is calibrated on a handful of examples**,
  not a labeled answerability dataset ([doc 3](03-evidence-gate.md)).
- **Ground-truth chunk IDs are hand-labeled and brittle.** They're tied to
  specific `document_id` values in a local database. Re-ingesting a
  document renumbers everything and silently invalidates the retrieval
  suite.

---

**Next:** [8. Open problems](08-open-problems.md)
