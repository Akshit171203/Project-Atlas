# 0. What to revise before working on this project

Written for the jump this project was built during: **full-stack developer
→ GenAI application developer.**

The good news is that most of a full-stack skill set transfers directly.
The genuinely new material is smaller than the field's vocabulary makes it
look — and a lot of what sounds essential (training models, transformer
internals, agent frameworks) is irrelevant to building something like
this.

Use this as a revision checklist. Each item says **why it matters here**,
with a pointer to where it shows up in the code, so you can check whether
you actually know it rather than whether you recognize the word.

---

## Part 1 — What already transfers

If you've built full-stack apps, you already have most of the following.
Skim, don't study.

| You know | It shows up here as |
|---|---|
| REST API design, status codes | FastAPI routes in [`app/api/`](../backend/app/api/) |
| CORS, preflight, origins | [`main.py`](../backend/app/main.py) — the first thing that breaks when wiring a frontend |
| `multipart/form-data` vs JSON | PDF upload vs `/query` — two different `fetch` shapes |
| Env-based config, secrets not in git | [`config.py`](../backend/app/core/config.py), `.env` |
| SQL, foreign keys, cascades | `ON DELETE CASCADE` is what makes document deletion clean up chunks and embeddings |
| Migrations | Alembic, same idea as any migration tool |
| Docker / compose | Postgres runs in a container |
| React state, props, conditional rendering | The whole frontend — no state library, just `useState` |
| Async/await (from JS) | Python's is similar in shape, different in mechanics — see below |

**Everything in [`INTEGRATION_NOTES.md`](../frontend/INTEGRATION_NOTES.md)
is standard full-stack work.** CORS, 204 responses with no body, error
shape consistency, type drift between backend and frontend. Nothing about
it is AI-specific. If that document feels easy, that's correct — it's
supposed to.

---

## Part 2 — Backend things that are *slightly* different

Not new concepts, but different enough to trip you up.

### Python `async` (if your async experience is JavaScript)

Same `async`/`await` keywords, different runtime model. Worth an hour.

- There's no single implicit event loop the way there is in a browser —
  `asyncio.run()` starts one, and code that blocks it blocks everything.
- **A CPU-bound call inside an `async def` blocks the whole loop.** This
  project's local models (embedding, reranker, NLI) are synchronous CPU
  calls sitting inside async functions. Fine for a single-user local tool;
  the first thing you'd fix for concurrency.
- `ContextVar` — used in
  [`llm_metrics.py`](../backend/app/services/llm_metrics.py) to collect
  per-request metrics without passing an object through every function.
  It's task-local storage; a module-level global would break under
  concurrent requests. Closest JS analogue is `AsyncLocalStorage`.

### SQLAlchemy 2.0 async + the repository pattern

If your ORM experience is Prisma/Sequelize/Django, SQLAlchemy 2.0's typed
`Mapped[]` style is a different dialect of the same ideas. You need:
sessions, `select()`, `await session.execute()`, eager loading
(`selectinload`) and why N+1 happens without it.

The repository layer in
[`app/repositories/`](../backend/app/repositories/) is just "keep queries
out of business logic." Nothing exotic.

### Pydantic

**Learn this properly — it's load-bearing.** It is not just validation
here:

- It defines the API contract, and FastAPI generates OpenAPI docs from it
  (`/docs`), which is what let the frontend's TypeScript types be written
  by hand without guessing.
- `BaseSettings` in [`config.py`](../backend/app/core/config.py) does
  typed env-var loading.
- `RAGResult` in [`schemas/rag.py`](../backend/app/schemas/rag.py) is the
  single object describing everything about an answer — text, per-claim
  verification, relevance, metrics, whether it was repaired or rejected.
  Read that one file and you understand the system's output.

### pgvector

A Postgres extension adding a `vector` column type and distance operators.
If you know Postgres, you know 90% of it. The remaining 10%: cosine
distance, and that approximate-nearest-neighbour indexes trade exactness
for speed.

---

## Part 3 — The genuinely new material

This is the part that's actually new. It is smaller than it looks.

### 3.1 Math — the honest minimum

You need far less than course syllabi suggest. **Four things:**

**Vectors as lists of numbers.** An embedding is a list of 384 floats.
That's it. No matrix calculus required.

**Dot product and cosine similarity.** Cosine measures the *angle* between
two vectors, ignoring their length: 1.0 = same direction, 0 =
perpendicular, -1 = opposite. Length usually encodes something irrelevant
(like text length), which is why angle is the right measure. When vectors
are normalized to length 1 — which
[`embedding.py`](../backend/app/services/embedding.py) does — cosine
similarity *is* the dot product. That's why the code can write
`similarity = 1 - distance` and trust it.

**Softmax.** Turns a list of arbitrary numbers into probabilities that sum
to 1. [`nli.py`](../backend/app/services/nli.py) implements it by hand in a
handful of lines — read that method, it's the clearest way to see what it
does. This is how three raw NLI outputs become "entailment 0.997, neutral
0.003, contradiction 0.000."

**Logits vs probabilities — the one that actually bit this project.** A
model's raw output layer produces *logits*: unbounded real numbers,
uncalibrated, not probabilities. Softmax converts them. A model that was
never softmaxed gives you numbers where **zero means nothing in
particular.**

> This caused a real bug. The evidence gate rejected any query whose best
> reranker score was below `0.0`, on the reasonable-sounding assumption
> that positive means relevant. But reranker scores are raw logits —
> measured, genuinely relevant matches scored as low as **-0.33**, while
> off-topic queries scored **-10.6**. The threshold sat inside the range
> good matches produce, so real questions were being refused. Full story
> in [doc 3](03-evidence-gate.md).

**You do not need:** backpropagation, gradient descent, loss functions,
attention math, matrix calculus, or how a transformer is built. Those
matter for *training* models. This project *uses* models.

### 3.2 Core LLM concepts

| Concept | Why it matters here |
|---|---|
| **Tokens** | The billing and latency unit. Not words — roughly 4 chars. Every cost decision in [doc 6](06-cost-and-latency.md) is denominated in these. |
| **Context window** | The finite prompt budget. The reason RAG exists instead of "paste the whole PDF." |
| **System vs user prompt** | System = standing rules, user = this request. Every prompt in [`app/prompts/`](../backend/app/prompts/) splits them deliberately. |
| **Temperature** | Randomness. `0.0` in the Ollama provider, because verification and evaluation should be as reproducible as possible. |
| **Non-determinism** | The same input can give different output. This is *why* an eval suite exists and why one run isn't proof. |
| **Hallucination** | The model produces fluent, confident, wrong text — indistinguishable by reading from correct text. The entire second half of this system exists because of this one property. |
| **Fine-tuning vs RAG** | Fine-tuning changes weights; RAG changes the prompt. Know why RAG is right for "answer questions about *this* document." |

### 3.3 Embeddings and vector search

- What an embedding model does: text → fixed-length vector, trained so
  similar meanings land close together.
- Why that beats keyword search: *"Where did coffee come from?"* matches
  *"The plant is native to the highlands of Ethiopia"* despite sharing no
  words.
- **Chunking**, and why it's unavoidable: you can't embed a 241-page book
  as one vector — the average of everything represents nothing.
- Approximate nearest neighbour search: why it's fast, and that it's
  approximate.

### 3.4 Bi-encoder vs cross-encoder — the single most important idea

If you learn one thing from this list, this is it. It explains the
architecture, and it's the biggest measured win in the project.

- **Bi-encoder** encodes query and document *separately* → vectors can be
  precomputed and indexed → scales to millions → but must compress a
  passage into one vector before knowing what will be asked.
- **Cross-encoder** reads query and document *together* → much more
  accurate → but nothing can be precomputed, so scoring a million
  documents means a million forward passes.
- Therefore: **bi-encoder for recall, cross-encoder to rerank the
  survivors.** Measured here — Recall@1 goes 0.435 → 0.826 from reranking
  alone.

Both the reranker and the NLI verifier in this project are
cross-encoders with different training objectives. Once that clicks, half
the codebase explains itself. → [doc 1](01-how-rag-works.md)

### 3.5 NLI (Natural Language Inference)

Premise + hypothesis → one of three labels: **entailment** (premise proves
it), **neutral** (premise neither proves nor disproves), **contradiction**
(premise disproves it).

The crucial subtlety: **neutral means "not supported," not "false."** A
claim can be perfectly true and still neutral, because that particular
sentence doesn't establish it. For a system promising "every statement is
backed by your document," neutral fails just like contradiction does.

This is how claims get verified without an LLM call. →
[doc 4](04-hallucination-and-verification.md)

### 3.6 Prompt injection

An LLM prompt has **no structural separation between instructions and
data** — it's one flat string. So text inside a user-uploaded PDF that
says *"ignore previous instructions"* reads to the model exactly like an
instruction.

If you know SQL injection, you have the right instinct — but note the
crucial difference: parameterized queries genuinely *solve* SQL injection
by separating data from instructions at the protocol level. **There is no
equivalent for prompts.** No `prepare()`. Defense is prompting plus
independent checks, never a guarantee. → [doc 5](05-relevance-and-prompt-injection.md)

### 3.7 Evaluation

- **Recall@k** — did a relevant result appear in the top k? (*Did we find
  it at all?*)
- **MRR** — average of 1/(rank of first relevant result). (*How high up?*)
- **Precision vs recall**, and that they trade off.
- Why "I tried it and it seemed better" is not evidence: two reasonable
  changes in this project made things measurably worse and were only
  caught by running the suite. → [doc 7](07-evaluation-methodology.md)

---

## Part 4 — Safe to skip

Explicitly, because this is where beginners lose weeks.

| Skip | Why |
|---|---|
| **Training or fine-tuning models** | This project trains nothing. Every model is downloaded and used as-is. |
| **Transformer internals, attention math** | Useful eventually. Not needed to build, debug, or explain any of this. |
| **CUDA, GPU optimization, quantization** | The local models run fine on CPU. |
| **LangChain / LlamaIndex** | This project deliberately uses **neither** — check [`pyproject.toml`](../backend/pyproject.toml). Every piece is written directly, which is *why* the failure modes in these docs were visible instead of hidden behind an abstraction. Learn the pieces first; frameworks are easier afterward, not before. |
| **Agents, tool use, function calling** | Different problem. Gemini's automatic function calling is explicitly *disabled* in [`llm.py`](../backend/app/services/llm.py). |
| **Vector database products** (Pinecone, Weaviate, Qdrant) | Concepts transfer from pgvector. Learn the idea, not a vendor. |
| **Model leaderboards, benchmark chasing** | Your 26-case eval on your own documents tells you more than MMLU does. |

---

## Part 5 — Misconceptions this project will correct

Things that sound true, that this codebase measured and found false. Worth
reading *before* you start, so you recognize them when they bite.

**"Semantic search understands meaning, so wording doesn't matter."**
The reranker here scored the same chunk **-10** for one phrasing and
**+3.00** for a paraphrase of the same question. It behaves much closer to
a strong fuzzy keyword matcher than a semantic reasoner.
→ [doc 2](02-retrieval-failures.md)

**"A higher score means more relevant, and positive means relevant."**
Only the first half is reliably true. Raw logits have no meaningful zero.
→ [doc 3](03-evidence-gate.md)

**"Retrieving more candidates is safer."**
Adding keyword search to the candidate pool made the eval suite go
**8/11 → 7/11**. Widening recall widens false positives too — and it
broke a query that was correctly being refused. → [doc 2](02-retrieval-failures.md)

**"If the retriever can't find it, it's probably not in the document."**
This exact inference was made in this project, and was wrong. The content
was there verbatim. A low retrieval score is evidence about *retrieval*,
never about the corpus. **Read the stored text before concluding
anything.** → [doc 2](02-retrieval-failures.md)

**"The LLM is where the bugs are."**
Two of the three current eval failures trace to **chunking** — a fact split
across a chunk boundary so no single chunk entails it, and an answer
sentence buried mid-chunk so it's never retrieved. Neither is fixed by a
better model. → [doc 8](08-open-problems.md)

**"If it passes verification, it's a good answer."**
An answer can be fully grounded, correctly cited, and still not answer the
question asked. That's a separate gate, and it's the one that caught a
prompt-injection attack that citation verification found nothing wrong
with. → [doc 5](05-relevance-and-prompt-injection.md)

---

## Part 6 — Self-check

If you can answer these without looking, you're ready to work on this
codebase. If not, the linked doc is where to go.

1. Why can't you embed an entire book as a single vector?
   → [doc 1](01-how-rag-works.md)
2. Why is a cross-encoder more accurate than a bi-encoder, and why can't
   you use one for the initial search? → [doc 1](01-how-rag-works.md)
3. Why is a rerank score of `-0.33` not evidence that a chunk is
   irrelevant? → [doc 3](03-evidence-gate.md)
4. What's the difference between an NLI result of `neutral` and one of
   `contradiction`, and why do both fail verification?
   → [doc 4](04-hallucination-and-verification.md)
5. Why does this pipeline check each claim against *every* retrieved
   source instead of the one the LLM cited?
   → [doc 4](04-hallucination-and-verification.md)
6. Why can't prompt injection be solved the way SQL injection was?
   → [doc 5](05-relevance-and-prompt-injection.md)
7. Why is a correct refusal counted as a *success* in the eval suite?
   → [doc 7](07-evaluation-methodology.md)
8. Why does this system take 73-80s per query, and which single change
   fixes most of it? → [doc 6](06-cost-and-latency.md)

---

## Part 7 — A suggested order

**Before touching the code** (~a weekend):

1. Cosine similarity and softmax — enough to read
   [`nli.py`](../backend/app/services/nli.py) and understand every line.
2. Tokens, context windows, system vs user prompts, temperature.
3. Embeddings and chunking, conceptually.
4. Bi-encoder vs cross-encoder — Part 3.4 above. Don't move on until this
   is solid.
5. NLI's three labels.

**Then read, in this order:**

1. [doc 1 — How RAG works](01-how-rag-works.md) — the mental model
2. [`rag.py`](../backend/app/services/rag.py) — the whole pipeline is one
   readable function; you'll recognize every stage from doc 1
3. [`schemas/rag.py`](../backend/app/schemas/rag.py) — what an answer
   actually contains
4. [doc 2](02-retrieval-failures.md) and [doc 3](03-evidence-gate.md) —
   the retrieval half
5. [doc 4](04-hallucination-and-verification.md) and
   [doc 5](05-relevance-and-prompt-injection.md) — the verification half
6. [doc 7](07-evaluation-methodology.md) — before you change anything
7. [doc 8](08-open-problems.md) — when you want something to work on

**Then, before your first change:** run
`scripts/evaluate_retrieval.py` (seconds, deterministic) and
`scripts/evaluate_rag.py` (~15 min). Knowing the numbers *before* you touch
anything is the whole discipline. Two changes in this project's history
looked like improvements and weren't.

---

**Next:** [1. How RAG works](01-how-rag-works.md)
