# 3. The evidence gate — deciding when *not* to answer

> Code: [`evidence_gate.py`](../backend/app/services/evidence_gate.py)
> (~30 lines). Investigation:
> [`EVIDENCE_GATE_CALIBRATION.md`](../backend/EVIDENCE_GATE_CALIBRATION.md).

## What it is and why it runs first

```python
return max(scores) >= self.min_rerank_score
```

That's the whole gate. Retrieval always returns *something* — vector
search returns the nearest chunks whether or not any of them are actually
relevant, because "nearest" is relative. Ask a coffee report about binary
search trees and you'll still get five coffee chunks back, just bad ones.

Without a gate, those five irrelevant chunks go to the LLM with the
instruction "answer using these sources," and the model does what models
do: produces something. Maybe it correctly says it can't. Maybe it
stretches. The system prompt asks it to refuse when sources are
insufficient, but that's a request, not a guarantee.

The gate turns that request into a mechanism. **If the best available
evidence isn't good enough, generation never runs.** That is: 0 LLM calls,
zero tokens, no latency, no chance of a hallucinated answer, because there
was no generation to hallucinate in. Refusing before you spend money is
strictly better than refusing after.

## The bug: a threshold that rejected real questions

`min_rerank_score` was originally `0.0` — which looks like the obvious
choice, because 0 is where scores stop being positive.

Two questions against a real 241-page book came back as *"I don't have
enough information in the knowledge base to answer this question"* with
**0 LLM calls** — the gate's signature:

1. *"summarise chapter 1 for me"*
2. *"what does author's father does?"*

Query 1 is the known summarization limitation ([doc 8](08-open-problems.md))
— expected. Query 2 is core content of that book. Worth investigating, not
writing off.

### Measuring instead of guessing

Rather than adjusting the threshold until things worked, the actual scores
got measured — querying `RerankedRetriever` directly, no LLM involved:

| Query | Best rerank score | Should it be answerable? |
|---|---|---|
| "who's the author of this book?" | **1.39** | yes — worked |
| "what does author's father does?" | **-0.33** | yes — wrongly rejected |
| "summarise chapter 1 for me" | **-3.42** | no — correctly rejected |
| Off-topic controls (different document) | **-10.6 to -11.3** | no |

The picture is immediate:

```
  -11        -10          -3.4        -0.33      1.4
   │──────────│            │            │─────────│
   off-topic              vague      ┌── genuinely relevant ──┐
                                     │
                            0.0 ─────┘  ← old threshold sat HERE,
                                           inside the "relevant" range
```

## The concept: cross-encoder scores are not probabilities

This is the piece worth internalizing, because it generalizes far past
this project.

A cross-encoder outputs a **raw logit** — an unbounded real number from
the final layer. Not a probability. Not calibrated. Not centered anywhere
in particular. `cross-encoder/ms-marco-MiniLM-L6-v2` was trained to *rank*
— to make relevant pairs score higher than irrelevant ones. That objective
constrains the *ordering* of scores and says nothing whatsoever about
their absolute values.

So "score > 0 means relevant" was never a property of this model. It was
an intuition imported from things that *are* calibrated — probabilities,
correlation coefficients, cosine similarity — where zero is a meaningful
boundary. Here, zero is just a number that happens to sit in the middle of
the range real matches produce.

The practical rule: **for any uncalibrated score, the threshold is an
empirical question about your model on your data, not a value you can
reason your way to.** You measure the distribution of known-good and
known-bad cases and put the line in the gap.

That's what `-2.0` is. Not a round number, not a default: the middle of
the observed gap between the relevant cluster (-0.33 to 1.4) and the
no-match cluster (-3.4 and below), with margin on both sides.

```
relevant:   -0.33 ────────► 1.4
                 ↑
gap:        -3.4 ─┴─ -0.33      ← -2.0 sits here
                 ↓
no match:  -11.3 ────────► -3.4
```

## Honesty about what this calibration is

It comes from a handful of real examples across two documents. It is not a
statistically derived threshold from a labeled dataset.

Doing it properly would mean assembling a few hundred deliberately labeled
answerable/unanswerable query-document pairs, plotting the score
distributions, and picking the threshold from the precision/recall
trade-off you actually want — probably favoring precision, since a wrong
answer costs more than a refusal in this system. That's a real next step
and it's written down as one rather than papered over.

The 11-case end-to-end suite includes off-topic negative controls
(`computer_virus`, `python_bst`) that exist specifically to catch a
threshold drifting too permissive, and
`summarize_chapter_known_limitation` guards the same boundary from the
other side. They're a regression guard, not a calibration set — but
they're what caught the keyword-merge experiment pushing a page-header
chunk to +0.503, over the line, and turning a correct refusal into an
answer.

## What the gate can't do

The gate reads one number: the best rerank score. Its quality is exactly
the quality of that number. From [doc 2](02-retrieval-failures.md):

- **A relevant chunk phrased unlike the question scores like noise.** No
  threshold separates a genuinely relevant chunk at -10 from an off-topic
  one at -10.6, because there's nothing there to separate. Query rewriting
  exists as the fallback for precisely this, and it runs *because* the
  gate said no — the gate is the trigger for the retry.
- **A junk chunk with heavy word overlap scores well.** The page-header
  chunk at +0.503 passed cleanly. Garbage in, confident yes out.

**A gate is a filter on a signal; it cannot be better than the signal.**
Improving refusal quality here means improving the reranker
([doc 2](02-retrieval-failures.md)), not tuning the number.

## What happened after the fix — a good illustration of layered gates

With `min_rerank_score=-2.0` and `top_k=5`, *"what does author's father
does?"* was re-run:

1. Retrieval now correctly surfaced the "Rich Dad's Advice" chunk. ✅
2. The model generated a grounded, correctly-cited answer from it —
   citation verification passed 5 of 6 claims. ✅
3. **The relevance check rejected it anyway.** Its reason: *"The answer
   does not address what the author's father does, but rather quotes Rich
   Dad's advice."*

That's correct behavior, not a leftover bug. The retrieved content covers
the father's *advice and philosophy*; the question asked about his
*occupation*. Related, adjacent, and not the same thing.

The retrieval fixes did their job — the right content reached the model.
A separate, independent layer then caught that **"grounded and correctly
cited" is not the same as "answers the question."** Both have to be true
before an answer is served, and here only one was. Different gates catch
different failures; that's the entire argument for having more than one.

---

**Next:** [4. Hallucination and verification](04-hallucination-and-verification.md)
