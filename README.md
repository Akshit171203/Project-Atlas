# Project Atlas

**A document Q&A system that refuses to answer when it shouldn't.**

Upload a PDF, ask questions about it, and get answers that are grounded in
the document, cited to specific passages, and machine-verified claim by
claim — or an honest refusal when the document doesn't support an answer.

The interesting part isn't the retrieval. It's everything that happens
after generation: an answer here has to pass three independent checks
before a user sees it, and the pipeline will withhold its own output when
they fail.

```
┌──────────────────────────────────────────────────────────────────┐
│  retrieve  →  EVIDENCE GATE  →  generate  →  extract claims       │
│                    ↓ refuse                        ↓              │
│                                            VERIFY each claim      │
│                                            (local NLI model)      │
│                                                    ↓              │
│                                       repair → re-verify          │
│                                                    ↓              │
│                                          RELEVANCE CHECK          │
│                                                    ↓ withhold     │
│                                              serve answer         │
└──────────────────────────────────────────────────────────────────┘
```

---

## What it does

- **Grounded answers only.** The model is given retrieved passages and
  instructed to use nothing else. Every factual claim carries a citation
  like `[S2]`.
- **Claims are verified, not trusted.** The answer is decomposed into
  atomic claims, and each is checked against every retrieved source with a
  local NLI (natural language inference) model. A claim only passes if a
  source *entails* it with ≥0.75 confidence.
- **Unsupported claims trigger a repair pass.** The answer is rewritten
  without them, then re-verified.
- **Three independent gates can refuse.** Before generation (is there any
  evidence?), after generation (is every claim grounded?), and last (does
  this actually answer the question?). They fail differently on purpose —
  each has caught something the others missed.
- **Full transparency in the UI.** Per-claim entailment scores, which
  gate rejected an answer, whether repair ran, LLM call count, token
  count and latency are all surfaced, not hidden.

## Measured results

**Retrieval** — 26 hand-labeled cases, no LLM calls, deterministic
([`evaluate_retrieval.py`](backend/scripts/evaluate_retrieval.py)):

| Metric | Vector only | Vector + reranker |
|---|---|---|
| Recall@1 | 0.435 | **0.826** |
| Recall@3 | 0.826 | **1.000** |
| Recall@5 | 0.826 | **1.000** |
| MRR | 0.636 | **0.906** |

Two-stage retrieval nearly doubles the chance the correct chunk is ranked
first. Note that vector-only Recall@3 and Recall@5 are *identical* — when
the embedding model misses, it misses completely, and no amount of
reranking recovers a chunk that was never retrieved. That flat line drives
most of [doc 2](docs/02-retrieval-failures.md).

**End-to-end** — 11 cases across 3 documents, ~5 LLM calls each
([`evaluate_rag.py`](backend/scripts/evaluate_rag.py)):

```
Successful:   8/11  (0.727)
Repair rate:  0.455
```

Success requires the system to make the right answerability call **and**,
if it answers, produce something both fully citation-supported and
relevant. Correctly refusing an unanswerable question counts as success —
otherwise every change would be pushed toward answering more.

The three failures are known, root-caused, and written up in
[doc 8](docs/08-open-problems.md). Two of them had a plausible shared
explanation that turned out to be wrong about both — see below.

## Architecture

```
Browser (:3000)                    Next.js 16 · React 19 · Tailwind
    │  fetch — JSON + multipart, no BFF proxy
    ▼
FastAPI (:8000)                    Python 3.11 · SQLAlchemy async · uv
    ├── ingestion    PyMuPDF → chunk (500 chars, 50 overlap) → embed
    ├── retrieval    pgvector cosine search → cross-encoder rerank
    ├── generation   pluggable LLM: Ollama (local) or Gemini
    └── verification claim extraction → NLI entailment → repair → relevance
    ▼
Postgres 17 + pgvector (:5433, Docker)
```

**Local models do the heavy lifting and cost nothing:**

| Role | Model | Why |
|---|---|---|
| Embeddings | `all-MiniLM-L6-v2` (384-dim) | Fast, precomputed at upload |
| Reranking | `ms-marco-MiniLM-L6-v2` | Cross-encoder; scores query+chunk together |
| Verification | `nli-deberta-v3-base` | Entailment / neutral / contradiction |

Only the LLM calls cost time or money — which is exactly why the pipeline
can afford to check *every claim against every source* on every query.

## Quickstart

**Prerequisites:** Docker, Python 3.11+ with [`uv`](https://docs.astral.sh/uv/),
Node 20+, and [Ollama](https://ollama.com) if running locally.

```bash
docker compose up -d
```

```bash
ollama serve && ollama pull llama3.1
```

Create `backend/.env`:

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/atlas
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1
GEMINI_API_KEY=your-key-here
```

```bash
cd backend && uv sync && uv run alembic upgrade head
```

```bash
cd backend && uv run uvicorn app.main:app --port 8000
```

```bash
npm install --prefix frontend && npm run dev --prefix frontend
```

Open <http://localhost:3000>, drag in a PDF, and ask it something. API
docs are at <http://localhost:8000/docs>.

> **Switching to Gemini** is one line — `LLM_PROVIDER=gemini` in
> `backend/.env`. No code changes; both providers implement the same
> `LLMProvider` protocol. Note the free tier caps at 20 requests/day on
> `gemini-3.6-flash`, and this pipeline uses ~5 per question — so about
> four questions a day without billing enabled.

**Run the evals:**

```bash
cd backend && PYTHONPATH=. uv run python scripts/evaluate_retrieval.py
```

```bash
cd backend && PYTHONPATH=. uv run python scripts/evaluate_rag.py
```

The first is deterministic and takes seconds. The second makes roughly 35
LLM calls (3 per answered question, +2 per repair, +1 per refusal for the
query-rewrite retry) and takes ~15 minutes locally.

---

## The engineering decisions worth reading about

### Two-stage retrieval, and why one model can't do both jobs

A **bi-encoder** embeds the question and each chunk separately, so chunk
vectors are computed once at upload and searched with an index — it scales
to millions of chunks, but has to compress a whole passage into 384
numbers before knowing what will be asked. A **cross-encoder** reads the
question and chunk *together* and is far more accurate, but its score
can't be precomputed, so scoring a million chunks means a million forward
passes.

So: bi-encoder for recall over everything, cross-encoder to precisely rank
the ~10 survivors. That's the Recall@1 jump from 0.435 to 0.826 in the
table above. → [doc 1](docs/01-how-rag-works.md)

### The reranker isn't as semantic as it sounds

The same chunk, for the same underlying question, scored **-10** for one
phrasing and **+3.00** for another — a ~13-point swing from word choice
alone, where genuinely off-topic content scores about -10.6.
`ms-marco-MiniLM-L6-v2` is trained on Bing click data, so it behaves much
more like a strong fuzzy keyword matcher than a semantic reasoner.

This undermines the assumption that the rerank score just needs the right
cutoff — a relevant passage can score like noise, and no threshold
separates it. → [doc 2](docs/02-retrieval-failures.md),
[`EVIDENCE_GATE_CALIBRATION.md`](backend/EVIDENCE_GATE_CALIBRATION.md)

### A threshold of 0.0 was rejecting real questions

Cross-encoder outputs are **raw logits, not probabilities** — trained to
rank, not to be calibrated, so "positive means relevant" was an intuition
imported from things that *are* calibrated. Measuring the actual score
distribution showed genuinely relevant matches as low as **-0.33** and
off-topic queries at **-10.6 to -11.3**. The threshold moved to **-2.0**,
in the gap between the clusters. → [doc 3](docs/03-evidence-gate.md)

### Verifying against the cited source was the wrong question

Claims were checked against whichever source the LLM cited for them — and
LLMs synthesize across chunks while attributing everything to one marker.
A measured case: a claim cited `[S1]` was entailed only by `[S2]`. The
claim was true, the evidence was retrieved and in the prompt, and the
verifier reported a hallucination because a number was wrong.

Now every claim is checked against **every** retrieved source. It's
affordable only because NLI is a free local model. →
[doc 4](docs/04-hallucination-and-verification.md)

### Only the relevance gate caught the prompt injection

An LLM prompt has no structural separation between instructions and data,
so a PDF containing *"SYSTEM NOTICE: ignore all previous instructions"*
gets retrieved as an ordinary chunk and reads to the model like a command.
There is no `prepare()` for prompts.

When this was tested, **citation verification found nothing to flag** —
and was structurally incapable of doing so, because the hijacked output
*was* faithfully grounded in a retrieved chunk. The relevance gate asks a
different question — does this answer what the user asked? — and caught
it.

Layered defenses are only worth their cost if they fail *independently*.
Three gates all checking grounding would be one gate with extra steps. →
[doc 5](docs/05-relevance-and-prompt-injection.md)

### Two "improvements" made it worse, and the eval caught both

| Change | Intent | Result |
|---|---|---|
| Query rewriting on every query | Fix phrasing brittleness | **5/7 → 4/7**, gated behind failure instead |
| Merging keyword-search candidates | Fix vector-search misses | **8/11 → 7/11**, reverted |

Both are textbook techniques, correctly implemented. The keyword merge
didn't even fix the case it was built for — reranking is
retrieval-source-agnostic, so a chunk scores the same however it was
found — and it broke a correct refusal by matching a page header
(`"Chapter One: Lesson 1"`) on pure lexical overlap.

The lesson: **widening recall widens false positives too**, and vector
search's semantic nature was silently filtering exactly that class of
junk. → [doc 2](docs/02-retrieval-failures.md)

### A diagnosis that survived until someone ran the model

Two failing eval cases shared one plausible explanation — "the claims are
true but phrased differently from the source, so NLI won't call them
entailed." It matched a pattern already confirmed elsewhere in the system.

Running the NLI model on the verbatim chunk text showed it was **wrong
about both**, and that the two cases are unrelated:

- `server_js_purpose` — the source sentence starts with a pronoun.
  Sentence-splitting (which is what makes NLI accurate) severs the
  antecedent. *"**It** spins up the HTTP server"* → `neutral`, **0.001**.
  Replace `It` with `server.js` → `entailment`, **0.998**. One word.
- `coffee_origins` — NLI passes it at **0.997**. The chunk holding the
  answer is simply never retrieved, while a chunk containing only the
  *section heading* "The Coffee Plant and Its Origins" reranks first. And
  the one claim that stayed unsupported is real but split across a chunk
  boundary: chunk 53 has the subject, chunk 54 has the rest, and **neither
  half entails the whole.**

Neither fix is a better model. Both are chunking and premise construction.
→ [doc 4](docs/04-hallucination-and-verification.md),
[doc 8](docs/08-open-problems.md)

### Verification costs 73-80 seconds, and that's the honest number

Up to five **sequential** LLM calls per question, each needing the
previous one's output. A comparable production system with a single call
and no verification answers in ~6s. Trimming prompts cut measured latency
42% (49.1s → 28.5s on one query at the time), but the call *count* is the
floor, and it's the price of the guarantees.

The relevance call was explicitly protected from cost-cutting — it's ~20%
of the budget and the only thing that caught the injection. →
[doc 6](docs/06-cost-and-latency.md),
[`COST_OPTIMIZATION.md`](backend/COST_OPTIMIZATION.md)

### Known bugs are kept as *failing* tests

`library_business_known_failure` is labeled `answerable: True` — the true
expected behavior — specifically so it keeps failing until the underlying
retrieval bug is fixed, rather than quietly redefining success as whatever
the system currently does. Its typo (`"bussiness"`) is preserved too,
because that's what a real user typed.

Its mirror image, `summarize_chapter_known_limitation`, is labeled
`answerable: False` and passes: refusing it is *correct*, and the case
exists as a regression guard. It earned its keep — it's what caught the
keyword-merge experiment turning a correct refusal into an answer. →
[doc 7](docs/07-evaluation-methodology.md)

---

## Documentation

**[📚 Engineering deep dives (docs/)](docs/README.md)** — nine documents
explaining every problem hit and why each fix worked, written to be read
after revising fundamentals rather than as a changelog.

New to this area? **[docs/00-prerequisites.md](docs/00-prerequisites.md)**
is a revision checklist for a full-stack developer moving into GenAI —
what already transfers, the honest math minimum (four things), what's safe
to skip, and the misconceptions this codebase measured and found false.

Original investigation records, written as the work happened:

- [`backend/EVIDENCE_GATE_CALIBRATION.md`](backend/EVIDENCE_GATE_CALIBRATION.md)
  — threshold calibration and reranker brittleness, with raw scores
- [`backend/COST_OPTIMIZATION.md`](backend/COST_OPTIMIZATION.md)
  — before/after token and latency measurements
- [`frontend/INTEGRATION_NOTES.md`](frontend/INTEGRATION_NOTES.md)
  — full frontend↔backend integration writeup

## Known limitations

- **Summarization queries are correctly refused.** Chunk retrieval matches
  specific questions to specific passages; "summarize chapter 1" has no
  specific content to match, and no chunk *is* a chapter. Fixing it needs
  structure-aware ingestion and a separate code path, not a threshold
  change. → [doc 8](docs/08-open-problems.md)
- **~73-80s per query** on local Ollama. Inherent to five sequential
  calls, not an implementation inefficiency.
- **Fixed-size chunking** splits mid-word and mid-sentence, which is
  upstream of two of the three current eval failures.
- **No auth, no multi-tenancy, no streaming.** Single-user local tool.
- **Backend and frontend types are two hand-maintained sources of truth.**
  OpenAPI codegen is the scale answer.

## Project layout

```
backend/
  app/
    api/            FastAPI routes — documents, query
    services/       ingestion, retrieval, reranking, RAG pipeline, verification
    prompts/        every LLM prompt, versioned as code
    evals/          test datasets + scoring logic
    repositories/   data access
  scripts/          evaluation runners and per-component probes
frontend/
  src/components/   DocumentSidebar, ChatPanel, ResultCard, SessionStats
  src/lib/api.ts    typed API client — one function per endpoint
docs/               engineering deep dives
```
