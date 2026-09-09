# Project Atlas — engineering deep dives

Written for someone coming back to this project after revising
fundamentals. Each document explains **why a problem happened and why the
fix worked**, not just what changed.

Read in order if you're new to RAG. Jump straight to a numbered document
if you're chasing something specific.

**New to GenAI and coming from another kind of development?** Start with
doc 0 — it's a revision checklist, including an explicit list of what you
can safely skip.

| # | Document | What it covers |
|---|---|---|
| 0 | [What to revise before starting](00-prerequisites.md) | Prerequisites for a full-stack dev moving into GenAI: what transfers, the honest math minimum, what to skip, and misconceptions this project will correct |
| 1 | [How RAG works, and why this system is built this way](01-how-rag-works.md) | Embeddings, cosine similarity, chunking, bi-encoders vs cross-encoders, NLI, why there are three refusal gates. **Start here.** |
| 2 | [Where retrieval breaks](02-retrieval-failures.md) | Keyword collision, vector search misses, the reranker's lexical brittleness, query rewriting, and the hybrid-search experiment that was reverted |
| 3 | [The evidence gate](03-evidence-gate.md) | Deciding when *not* to answer; why cross-encoder scores aren't probabilities and thresholds must be measured |
| 4 | [Hallucination and verification](04-hallucination-and-verification.md) | Claim extraction, NLI entailment, the citation-misattribution bug, repair, and two failing cases whose shared diagnosis turned out to be wrong about both |
| 5 | [Relevance and prompt injection](05-relevance-and-prompt-injection.md) | LLM-as-judge, and why the relevance gate — not citation verification — was the layer that caught a prompt-injection attack |
| 6 | [Cost and latency](06-cost-and-latency.md) | Why five sequential LLM calls cost 73-80s, what was optimized, what was deliberately left alone, and the pluggable provider design |
| 7 | [Evaluation methodology](07-evaluation-methodology.md) | Recall@k and MRR, what "success" means end-to-end, and the discipline of keeping known bugs as *failing* test cases |
| 8 | [Open problems](08-open-problems.md) | The three current failures, each root-caused, with what would fix them and in what order |

## The original investigation records

These are the primary sources — written as the work happened, with the raw
measurements. The numbered docs above explain the concepts behind them.

- [`backend/EVIDENCE_GATE_CALIBRATION.md`](../backend/EVIDENCE_GATE_CALIBRATION.md)
  — threshold calibration from real scores, the discovery of reranker
  lexical brittleness, and the keyword-search experiment that was tried
  and reverted with the measured reason
- [`backend/COST_OPTIMIZATION.md`](../backend/COST_OPTIMIZATION.md)
  — before/after token and latency measurements, and the `top_k=3` change
  that improved the numbers and was reverted anyway
- [`frontend/INTEGRATION_NOTES.md`](../frontend/INTEGRATION_NOTES.md)
  — the full frontend↔backend integration writeup: CORS, multipart vs
  JSON, 204 handling, type drift, and the rest

## If you only read three things

1. **[Doc 1's bi-encoder/cross-encoder section](01-how-rag-works.md#two-stage-retrieval-bi-encoders-and-cross-encoders)**
   — the idea that does the most work in this system, with the measured
   Recall@1 jump from 0.435 to 0.826 that proves it.
2. **[Doc 2's "tried and reverted"](02-retrieval-failures.md#tried-and-reverted-merging-keyword-search-into-the-candidate-pool)**
   — a textbook technique, correctly implemented, that made things worse
   for a reason worth understanding: widening recall widens false
   positives too.
3. **[Doc 4's corrected diagnosis](04-hallucination-and-verification.md#where-verification-still-fails--and-a-diagnosis-that-turned-out-wrong)**
   — two failures that looked identical, shared one plausible
   explanation, and turned out to be unrelated bugs. Neither matched the
   explanation.
