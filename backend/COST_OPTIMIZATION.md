# Token/latency cost optimization

What was actually changed to reduce per-query LLM cost, why, and what it
measured — kept as a real before/after record, not a design doc written in
advance of doing the work.

> **Update:** the `top_k=5 → 3` change documented below was later
> **reverted back to 5** after it caused a real retrieval failure on a
> different, harder document (a specific, well-supported question ranked
> the correct chunk 4th, past the `top_k=3` cutoff). See
> [`EVIDENCE_GATE_CALIBRATION.md`](EVIDENCE_GATE_CALIBRATION.md) for the
> full investigation. The `LLM_MAX_OUTPUT_TOKENS` cap and the
> measurements below are still accurate for what they measured — just
> know that `top_k` is currently 5, not 3, in the live pipeline. This is
> left in place rather than rewritten, because the trade-off it documents
> (and the fact that it didn't hold up) is itself the useful part.

## Where the cost was coming from

Every `/query` call runs up to 5 sequential LLM calls (see
[`app/services/rag.py`](app/services/rag.py)):

1. **Generate** — compose the answer from retrieved chunks
2. **Extract claims** — pull factual claims out of the answer, for
   verification
3. **Repair** *(only if verification found unsupported claims)* — rewrite
   the answer
4. **Extract claims again** *(only if repaired)* — re-verify the repaired
   answer
5. **Relevance** — judge whether the final answer actually addresses the
   question

Steps 1 and 3 both include the full retrieved context in their prompt —
meaning the same source text gets paid for twice on any query that needs
repair. Per-claim citation verification itself (the NLI cross-encoder in
[`citation_verifier.py`](app/services/citation_verifier.py)) is a local
model call, not an LLM call — free in token terms. The token cost is
entirely in the 5 LLM round-trips.

## Baseline (before this change)

Measured directly, not estimated — query `"How do arabica and robusta
differ?"` against the coffee report document, `LLM_PROVIDER=ollama`,
`llama3.1`:

```json
{ "llm_call_count": 5, "total_duration_seconds": 49.12, "total_tokens": 3245 }
```

## Changes made

### 1. Reduced retrieved chunk count: `top_k=5` → `top_k=3`

[`app/services/rag.py`](app/services/rag.py) — `RerankedRetriever.retrieve()`
call inside `RAGService.answer()`. Each chunk is ~500 characters
(`chunk_size=500` in [`app/services/chunking.py`](app/services/chunking.py)),
so this trims roughly 250 tokens of source context from *every* call that
includes it — generation and repair, i.e. 2 of the 5 calls.

**Trade-off:** fewer candidate chunks means less redundancy if the top-3
rerank picks are imperfect — a real risk on ambiguous queries where the
correct supporting passage might rank 4th or 5th. Not observed in testing
here, but worth watching if answer quality regresses on a broader eval run.

### 2. Explicit output token cap: `LLM_MAX_OUTPUT_TOKENS=500`

New setting in [`app/core/config.py`](app/core/config.py), applied in both
providers in [`app/services/llm.py`](app/services/llm.py):
- `GeminiProvider`: `max_output_tokens` in the `generate_content` config
- `OllamaProvider`: `max_tokens` in the OpenAI-compatible `chat.completions.create` call

Neither provider had any cap before this — nothing stopped a model from
rambling into a much longer completion than needed. This is exactly what
we saw earlier in the session: `llama3.1` once appended an unprompted
"Note: I removed the claims about..." explanation to a repaired answer,
inflating that call's completion token count for no benefit. The cap
bounds worst-case cost regardless of how well-behaved the model's output
is, independent of prompt-engineering fixes.

**Trade-off:** 500 tokens is enough for every case observed in this
session's testing (answers, repairs, and claim-extraction JSON all fit
comfortably under it), but it's a hard limit — a legitimately long,
well-supported answer with many citations could get cut off mid-response
on a more complex document. Chosen as a reasonable default, not derived
from a formal analysis of expected claim/citation volume.

## Result — same query, same model, after both changes

```json
{ "llm_call_count": 5, "total_duration_seconds": 28.46, "total_tokens": 2682 }
```

| | Before | After | Change |
|---|---|---|---|
| Tokens | 3,245 | 2,682 | **−17.3%** |
| Duration | 49.12s | 28.46s | **−42.1%** |
| LLM calls | 5 | 5 | unchanged |

## Full eval suite — did quality survive the cost cuts?

Ran the same 7-case suite (`scripts/evaluate_rag.py`) used to establish
Stage 1's baseline numbers, before and after these two changes, on the
same document set:

| | Before (top_k=5, no output cap) | After (top_k=3, 500-token cap) |
|---|---|---|
| Success rate | 5/7 (71.4%) | **6/7 (85.7%)** |
| Repair rate | 4/7 (57.1%) | **2/7 (28.6%)** |

Quality didn't just survive the cost cuts — it improved, and the repair
rate roughly halved. The likely explanation: a smaller, more tightly
curated set of retrieved chunks (top-3 instead of top-5) gives the model
less irrelevant material to accidentally draw an unsupported claim from
on the *first* pass, so fewer answers need fixing at all. This is a
plausible mechanism, not a proven one from a single 7-case run — worth
re-confirming on a larger eval set before treating "fewer chunks → better
answers" as a general rule rather than something observed on this
document.

The one persistent failure (`arabica_robusta`, citations not fully
supported even after repair) failed in both runs — the same underlying
repair-quality gap noted earlier in this project's history, not something
introduced by this change.

Latency dropped more than tokens did — smaller prompts mean less for the
model to process *and* generate, so the win compounds beyond the raw
token-count reduction. Call count is unchanged; these two fixes only trim
what each call costs, not how many calls happen.

**One thing observed, not hidden:** post-repair citation verification came
back with zero extracted claims on this run (`"verifications": []`),
where the same query pre-optimization successfully extracted claims at
every step. Plausibly the shorter, more concise repaired answer (itself a
side effect of the tighter token budget) was harder for the claim
extractor to parse into structured JSON — or it's simply run-to-run
variance in a non-deterministic local model. It didn't affect the served
answer, because the relevance check (not citation verification) is the
final gate before an answer is withheld — see the `rejected` field in
`RAGResult` and the prompt-injection hardening earlier in this project's
history. Worth watching for a pattern across more queries before treating
it as a real regression.

## What wasn't touched, and why

- **The relevance evaluation call (step 5).** This is the one signal that
  caught a real prompt-injection attack earlier (see the injection test —
  citation verification found nothing to flag, only relevance correctly
  scored the hijacked answer as irrelevant). Cutting it would save one
  full call's worth of tokens but reopens a vulnerability that was
  deliberately closed. Not a good trade.
- **Merging claim-extraction into the generation call.** The highest-
  leverage remaining option — it would remove an entire call (not just
  shrink one), since generation and claim-extraction currently run as two
  separate round-trips. Not done here because it changes the *shape* of
  the pipeline (the model would need to return structured
  `{answer, claims}` output directly) and risks lower-quality claim
  extraction if a single call is asked to both compose fluent prose and
  rigorously enumerate its own factual claims in one shot. Needs a real
  quality comparison (repair rate, citation-verification accuracy) before
  committing to it — flagged as a follow-up, not implemented speculatively.
- **Parallelizing independent calls (e.g. relevance alongside
  verification).** Would help wall-clock latency on a cloud provider like
  Gemini (genuine request concurrency), but not on local Ollama — a single
  loaded model on one GPU processes one request at a time regardless of
  how many are issued concurrently, so this wouldn't have shown any
  measurable win in the environment these numbers were captured in.
