# 1. How RAG works, and why this system is built the way it is

> Start here. Everything in the other documents assumes the vocabulary and
> the mental model in this one.

## The problem RAG actually solves

An LLM knows what was in its training data. It does not know what is in
*your* PDF. If you ask it about a document it has never seen, one of three
things happens: it says it doesn't know, it hallucinates something
plausible, or it answers from some vaguely related thing it saw during
training and presents it with full confidence.

There are three ways to give a model knowledge it doesn't have:

| Approach | What it does | Why it's wrong here |
|---|---|---|
| **Fine-tuning** | Adjust the model's weights on your data | Expensive, slow, has to be redone on every document change, and the model still can't tell you *where* an answer came from |
| **Stuff everything in the prompt** | Paste the whole document into context | A 241-page book is far past a comfortable context budget; you pay for every token on every question; and models get measurably worse at finding a needle in a very long haystack |
| **Retrieval-Augmented Generation** | Find the few passages relevant to *this* question, put only those in the prompt | What this project does |

RAG is, at heart, *search plus prompt assembly*. The "AI" part of finding
the right passage is a search problem. The LLM's job is narrowed from
"know everything" to "read these five paragraphs and answer using only
them" — a much easier job, and one you can check.

That last part is the whole point of Project Atlas. If the model is only
allowed to use text you handed it, then every claim it makes is checkable
against that text. A general-purpose chatbot's answer is unfalsifiable.
A RAG answer is not.

## The two halves: ingestion and query

### Ingestion (happens once per document, at upload)

```
PDF file
  │  PyMuPDF — extract text, page by page
  ▼
Raw text per page
  │  ChunkingService — split into ~500-character pieces, 50-char overlap
  ▼
Chunks (rows in the `chunks` table)
  │  sentence-transformers/all-MiniLM-L6-v2 — encode each chunk
  ▼
384-dimension vectors (rows in the `embeddings` table, pgvector column)
```

### Query (happens on every question)

```
User question
  │  same embedding model — encode the question
  ▼
Query vector
  │  pgvector — cosine-distance search over stored chunk vectors
  ▼
~10 candidate chunks
  │  cross-encoder/ms-marco-MiniLM-L6-v2 — rescore each (question, chunk) pair
  ▼
top 5 chunks
  │  evidence gate — is the best score good enough to answer at all?
  ▼
LLM generate → extract claims → NLI-verify each claim → repair → re-verify
  ▼
relevance check → serve or withhold
```

Everything after "top 5 chunks" is the verification machinery, covered in
docs [4](04-hallucination-and-verification.md) and
[5](05-relevance-and-prompt-injection.md). The rest of this document
explains the retrieval half, because retrieval quality sets a ceiling that
no amount of clever prompting can raise: **if the right passage isn't in
the top 5, the model literally cannot give a correct grounded answer.**

## Embeddings: turning text into geometry

An embedding model maps a piece of text to a fixed-length list of numbers
— here, 384 of them. The training objective is what makes this useful:
these models are trained so that **texts with similar meaning land close
together** in that 384-dimensional space, and unrelated texts land far
apart.

So "Where did coffee come from?" and "Coffee is native to the highlands of
Ethiopia" end up near each other even though they share almost no words.
That's the thing keyword search cannot do, and it's why vector search is
the default first stage in RAG.

### Cosine similarity, concretely

Closeness is measured by the **angle** between two vectors, not the
distance between their tips. Two vectors pointing the same direction have
cosine similarity 1.0; perpendicular is 0.0; opposite is -1.0.

Angle rather than distance matters because vector *length* tends to encode
something irrelevant, like how long the text is. You want "these mean the
same thing," not "these are the same size."

In [`embedding.py`](../backend/app/services/embedding.py) the vectors are
stored with `normalize_embeddings=True`, meaning every vector is scaled to
length 1. Once all vectors are unit length, cosine similarity is just the
dot product, and pgvector's `cosine_distance` (which is `1 - similarity`)
becomes cheap and well-behaved. That's why
[`retrieval.py`](../backend/app/services/retrieval.py) computes
`similarity = 1 - distance` and can trust the result to sit in a sane
range.

### Why pgvector instead of a dedicated vector database

Pinecone, Weaviate, Qdrant and friends are purpose-built for this. But
this project already needed Postgres for documents, chunks and metadata,
and pgvector adds vector columns and an ANN index to that same database.
One datastore means one connection pool, one migration story, real foreign
keys with `ON DELETE CASCADE` (deleting a document actually removes its
chunks and embeddings), and the ability to filter by `document_id` in the
*same* SQL query as the vector search — see
[`embedding_repository.py`](../backend/app/repositories/embedding_repository.py).

That last point matters more than it sounds. Per-document querying is a
core feature of this app, and in a separate vector store it's a metadata
filter that may or may not compose well with the ANN index. In Postgres
it's a `WHERE` clause.

## Chunking: the decision that quietly limits everything

You cannot embed a 241-page book as one vector. A single 384-number vector
that has to represent an entire book represents nothing in particular —
it averages all its topics into mush, and it will be moderately close to
every query and precisely close to none.

So documents get split. [`chunking.py`](../backend/app/services/chunking.py)
uses a fixed ~500-character window with 50 characters of overlap, split on
whitespace so words aren't cut in half, and never spanning a page boundary.

**Why overlap exists:** a hard split at character 500 can land in the
middle of the one sentence that answers the question, leaving half the
fact in chunk N and half in chunk N+1 — and neither chunk on its own
supports the claim. Overlap means the boundary region appears in full in
at least one chunk. It costs some storage and some duplicate retrieval; it
buys insurance against the worst chunking failure mode.

**What this simple scheme costs.** More than it looks — the single most
expensive limitation in the system traces back here.

The end position backs off to a whitespace boundary, but the *start*
position advances by a flat `chunk_size - overlap`, so chunks routinely
begin mid-word: chunk 43 in the local database starts `"romatic flavor"`,
chunk 44 starts `"ivation spread across the Red Sea"`. Sentences get split
across boundaries too — one fact about Gabriel de Clieu has its subject in
chunk 53 and its object in chunk 54, and consequently **no single chunk
entails it**, so verification marks a perfectly real fact unsupported.
Chunk 43 is also the chunk holding the answer to a failing eval case, and
it's never retrieved, partly because its first half is about a different
topic entirely. That whole chain is traced in
[doc 4](04-hallucination-and-verification.md).

Beyond the boundary placement, fixed-size chunking is structure-blind. It doesn't know what a paragraph is, or a section, or a
chapter. A chunk can be half of one idea and half of the next. A page
header (`"Chapter One: Lesson 1"`) becomes its own chunk that looks, to a
lexical matcher, exactly like a chapter's content — this exact chunk
caused a real regression, documented in
[doc 2](02-retrieval-failures.md). And nothing in the system can answer
"summarize chapter 1," because no chunk *is* chapter 1 and retrieval only
ever returns chunks.

Better schemes exist — recursive splitting on paragraph/sentence
boundaries, semantic chunking that splits where the embedding shifts,
document-structure-aware chunking that keeps headings attached to their
sections. None are implemented here. Knowing *why* you'd want them is
worth more than having implemented one: **chunking is the point where you
decide what your system's smallest answerable unit is, and you cannot
answer a question that spans more than a handful of those units.**

## Two-stage retrieval: bi-encoders and cross-encoders

This is the single most important architectural idea in the retrieval half
of the system, and it's the one that most obviously pays off in the eval
numbers.

### Bi-encoder (the embedding model)

A bi-encoder encodes the question and the chunk **separately**, then
compares the two vectors.

```
encode("where did coffee originate?") ──► [0.02, -0.41, ...]  ┐
                                                              ├─ cosine
encode("Coffee is native to Ethiopia") ─► [0.05, -0.38, ...]  ┘
```

The critical property: the chunk side does not depend on the query, so
**every chunk's vector can be computed once at upload time and stored.**
At query time you encode one short string and do a vector index lookup.
This scales to millions of chunks.

The cost: the model must compress an entire chunk into one vector *before
it knows what will be asked about it*. Everything the chunk says about
anything has to fit into 384 numbers. Nuance gets averaged away.

### Cross-encoder (the reranker)

A cross-encoder takes the question and the chunk **together**, as one
input, and outputs a single relevance score.

```
score("where did coffee originate?" ⊕ "Coffee is native to Ethiopia") ──► 4.2
```

Because the model sees both texts at once, its attention layers can relate
individual words in the question to individual words in the passage. It is
substantially more accurate.

The cost is brutal and unavoidable: the score depends on the pair, so
**nothing can be precomputed.** Scoring a query against a million chunks
means a million forward passes. That's not a search engine, that's a
batch job.

### So you use both

```
1,000,000 chunks
   │  bi-encoder + ANN index — fast, approximate, precomputed
   ▼
10 candidates          ← candidate_k=10
   │  cross-encoder — slow, accurate, 10 forward passes
   ▼
5 chunks               ← top_k=5
```

The bi-encoder's job is **recall**: get the right chunk *somewhere* in the
candidate pool. The cross-encoder's job is **precision**: sort that small
pool properly. Neither can do the other's job at acceptable cost.

**This is not theoretical — it's the biggest measured win in the project.**
Across the 26-case retrieval suite
([`evaluate_retrieval.py`](../backend/scripts/evaluate_retrieval.py)):

| Metric | Vector only | Vector + reranker |
|---|---|---|
| Recall@1 | 0.435 | **0.826** |
| Recall@3 | 0.826 | **1.000** |
| Recall@5 | 0.826 | **1.000** |
| MRR | 0.636 | **0.906** |

Read Recall@1 first: vector search alone puts the right chunk in the top
slot **43.5%** of the time. Add the reranker and it's **82.6%** — the
correct chunk nearly doubles its chance of being ranked first, with no
change to what was retrieved, only to how it was ordered.

Then read Recall@3 vs Recall@5 for vector-only: both **0.826**, identical.
That flat line is the bi-encoder's ceiling — in the ~17% of cases it
fails, the right chunk isn't at rank 4 or 5 either; it's *not in the top
10 at all*. Reranking cannot fix that, because a reranker can only reorder
what it was given. The two stages fail in genuinely different ways, and
[doc 2](02-retrieval-failures.md) is largely about what happens when the
first stage misses.

> **Metric definitions.** *Recall@k* = the fraction of queries where at
> least one genuinely relevant chunk appears in the top k results. It
> answers "did we find it at all?" *MRR* (Mean Reciprocal Rank) = the
> average of 1/(rank of the first relevant result). Rank 1 scores 1.0,
> rank 2 scores 0.5, rank 5 scores 0.2. It answers "how high up did we
> find it?" Recall is about the LLM having a chance; MRR is about how much
> irrelevant material it has to read first.

## NLI: the model that checks the answer

One more model type, used after generation rather than during retrieval.

**Natural Language Inference** takes a *premise* and a *hypothesis* and
classifies the relationship between them into exactly one of three labels:

| Label | Meaning | Example (premise → hypothesis) |
|---|---|---|
| **entailment** | If the premise is true, the hypothesis must be true | "Light roasts preserve brighter acidity" → "Light roasts preserve acidity" |
| **neutral** | The premise neither proves nor disproves it | "Light roasts preserve brighter acidity" → "Light roasts have more caffeine" |
| **contradiction** | If the premise is true, the hypothesis must be false | "Coffee comes from the genus Coffea" → "Coffee is grown on Mars" |

Note what "neutral" means: **not supported**, which is not the same as
false. The claim about caffeine might be perfectly true — it just isn't
established by that sentence. For a system whose promise is "every
statement is backed by your document," neutral and contradiction are both
failures, and only entailment passes. Those four rows above are literally
the citation eval cases in
[`citation_dataset.py`](../backend/app/evals/citation_dataset.py).

This project uses `cross-encoder/nli-deberta-v3-base`, another
cross-encoder — same architecture idea as the reranker, different training
objective. It runs locally and free, which is what makes it affordable to
check *every claim against every retrieved source* on every query. Doc
[4](04-hallucination-and-verification.md) covers how that gets used and
where it breaks.

## Why there are so many gates

A plain RAG system is: retrieve, prompt, return. This one has three
independent places where it can refuse to answer:

1. **The evidence gate** (before generation) — is there anything relevant
   enough to answer from? → [doc 3](03-evidence-gate.md)
2. **Citation verification + repair** (after generation) — is every claim
   actually entailed by a retrieved source? →
   [doc 4](04-hallucination-and-verification.md)
3. **The relevance check** (last) — does the answer address the question
   that was asked? → [doc 5](05-relevance-and-prompt-injection.md)

They exist because they fail differently, and each has caught something
the others missed. The evidence gate catches "nothing in the document is
about this." Citation verification catches "the model made something up."
The relevance check catches "the model produced fluent, well-cited text
that answers a different question" — including, in one real test, an
answer hijacked by instructions embedded in the source PDF, which
citation verification found nothing wrong with because the hijacked text
was faithfully drawn from the source.

**"I don't know" is a feature.** A system that always answers is a system
whose answers carry no information — you can't distinguish a confident
correct answer from a confident wrong one. Every gate here trades some
recall (questions that could have been answered but weren't) for the
ability to trust the answers that do come out.

---

**Next:** [2. Where retrieval breaks](02-retrieval-failures.md)
