==============================================================================
PROJECT ATLAS - ENGINEERING DEEP DIVES
==============================================================================

Written for someone coming back to this project after revising fundamentals.
Each document explains why a problem happened and why the fix worked, not just
what changed.

Read in order if you're new to RAG. Jump straight to a numbered document if
you're chasing something specific.

New to GenAI and coming from another kind of development? Start with doc 0 -
it's a revision checklist, including an explicit list of what you can safely
skip.

  # | Document                                     | What it covers
  --+----------------------------------------------+--------------------------
  0 | What to revise before starting               | Prerequisites for a
    | [docs/00-prerequisites.txt]                  | full-stack dev moving
    |                                              | into GenAI: what
    |                                              | transfers, the honest
    |                                              | math minimum, what to
    |                                              | skip, and misconceptions
    |                                              | this project will correct
  1 | How RAG works, and why this system is built  | Embeddings, cosine
    | this way [docs/01-how-rag-works.txt]         | similarity, chunking,
    |                                              | bi-encoders vs
    |                                              | cross-encoders, NLI, why
    |                                              | there are three refusal
    |                                              | gates. Start here.
  2 | Where retrieval breaks                       | Keyword collision, vector
    | [docs/02-retrieval-failures.txt]             | search misses, the
    |                                              | reranker's lexical
    |                                              | brittleness, query
    |                                              | rewriting, and the
    |                                              | hybrid-search experiment
    |                                              | that was reverted
  3 | The evidence gate                            | Deciding when not to
    | [docs/03-evidence-gate.txt]                  | answer; why cross-encoder
    |                                              | scores aren't
    |                                              | probabilities and
    |                                              | thresholds must be
    |                                              | measured
  4 | Hallucination and verification               | Claim extraction, NLI
    | [docs/04-hallucination-and-verification.txt] | entailment, the
    |                                              | citation-misattribution
    |                                              | bug, repair, and two
    |                                              | failing cases whose
    |                                              | shared diagnosis turned
    |                                              | out to be wrong about
    |                                              | both
  5 | Relevance and prompt injection               | LLM-as-judge, and why the
    | [docs/05-relevance-and-prompt-injection.txt] | relevance gate - not
    |                                              | citation verification -
    |                                              | was the layer that caught
    |                                              | a prompt-injection attack
  6 | Cost and latency                             | Why five sequential LLM
    | [docs/06-cost-and-latency.txt]               | calls cost 73-80s, what
    |                                              | was optimized, what was
    |                                              | deliberately left alone,
    |                                              | and the pluggable
    |                                              | provider design
  7 | Evaluation methodology                       | Recall@k and MRR, what
    | [docs/07-evaluation-methodology.txt]         | "success" means
    |                                              | end-to-end, and the
    |                                              | discipline of keeping
    |                                              | known bugs as failing
    |                                              | test cases
  8 | Open problems [docs/08-open-problems.txt]    | The three current
    |                                              | failures, each
    |                                              | root-caused, with what
    |                                              | would fix them and in
    |                                              | what order

THE ORIGINAL INVESTIGATION RECORDS
==================================

These are the primary sources - written as the work happened, with the raw
measurements. The numbered docs above explain the concepts behind them.

  - backend/EVIDENCE_GATE_CALIBRATION.md - threshold calibration from real
    scores, the discovery of reranker lexical brittleness, and the keyword-
    search experiment that was tried and reverted with the measured reason
  - backend/COST_OPTIMIZATION.md - before/after token and latency
    measurements, and the top_k=3 change that improved the numbers and was
    reverted anyway
  - frontend/INTEGRATION_NOTES.md - the full frontend↔backend integration
    writeup: CORS, multipart vs JSON, 204 handling, type drift, and the rest

IF YOU ONLY READ THREE THINGS
=============================

  1. Doc 1's bi-encoder/cross-encoder section [docs/01-how-rag-works.txt] -
     the idea that does the most work in this system, with the measured
     Recall@1 jump from 0.435 to 0.826 that proves it.
  2. Doc 2's "tried and reverted" [docs/02-retrieval-failures.txt] - a
     textbook technique, correctly implemented, that made things worse for a
     reason worth understanding: widening recall widens false positives too.
  3. Doc 4's corrected diagnosis [docs/04-hallucination-and-verification.txt]
     - two failures that looked identical, shared one plausible explanation,
     and turned out to be unrelated bugs. Neither matched the explanation.
