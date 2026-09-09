# Connecting the frontend to the backend — full process

An interview-ready walkthrough of everything required to go from "two
separate codebases" to "a working full-stack app" — not just the bugs we
hit, but the actual sequence of decisions and setup involved. Project Atlas
is two independent processes: a FastAPI backend (`:8000`) and a Next.js
frontend (`:3000`), talking over plain HTTP from the browser. Nothing here
is framework magic — it's the same integration work you'd do connecting any
SPA to any REST API.

## 1. Architecture: who talks to whom

```
Browser (localhost:3000)
   │  fetch() calls, JSON + multipart
   ▼
Next.js dev server (serves the React app, no API logic of its own)
   │
   ▼ (all backend calls happen client-side, straight from the browser)
FastAPI backend (localhost:8000)
   │
   ▼
Postgres + pgvector, local embedding/reranker/NLI models, Gemini/Ollama
```

The frontend is a pure client — it holds no server secrets, does no
database access, and doesn't proxy requests through Next.js API routes. The
browser calls the FastAPI backend directly. That choice is *why* CORS (§3)
was the first thing that had to be solved: a browser enforces cross-origin
rules; a server-to-server proxy wouldn't have hit that at all. Worth being
able to explain that trade-off — direct-to-backend is simpler here, but a
BFF (backend-for-frontend) proxy layer is the usual answer once you need to
hide API keys from the browser or aggregate multiple backend calls.

## 2. What the backend had to expose before a frontend could exist

The backend was built API-first, and it genuinely wasn't frontend-ready
until these were in place:

1. **A stable, versioned request/response contract.** `RAGResult`,
   `DocumentRecord`, `QueryRequest` etc. are Pydantic models — FastAPI
   auto-generates OpenAPI docs from them (`/docs`), which is what made it
   possible to write the frontend's TypeScript types by hand without
   guessing field names.
2. **CRUD, not just the "interesting" endpoint.** The core RAG pipeline
   (`/query`) existed long before `GET /documents` or
   `DELETE /documents/{id}` did — those only got added once a UI needed to
   *list* and *manage* documents, not just query one. Easy to forget these
   until a real client forces the question "how does the user see what
   they've already uploaded?"
3. **CORS middleware.** Without `CORSMiddleware`, every browser request
   from `:3000` to `:8000` fails before it even reaches route code — the
   browser blocks it. This has to be added on the *backend*, and it has to
   explicitly allow-list the frontend's origin (see §3.1).
4. **Consistent error responses.** `HTTPException(status_code=..., detail=...)`
   everywhere, so the frontend can rely on `{"detail": "..."}` as the error
   shape rather than parsing arbitrary tracebacks.

## 3. What the frontend had to set up to consume it

1. **A typed API client** (`src/lib/api.ts`) — one function per endpoint,
   each returning a typed Promise, with a single shared `handleResponse`
   that centralizes error handling and content-type quirks (see §4). This
   is the layer that isolates the rest of the app from ever calling
   `fetch()` directly.
2. **Environment-based configuration.** The backend URL isn't hardcoded —
   it's `process.env.NEXT_PUBLIC_API_URL`, set in `.env.local`. This is
   what makes the same frontend buildable against a local backend today and
   a deployed one later without code changes.
3. **State management for two independent resources.** Documents (list,
   selection, upload, delete) and chat messages (per-document history) are
   modeled as separate React state in `page.tsx`, composed into child
   components (`DocumentSidebar`, `ChatPanel`) that receive data and
   callbacks as props rather than each doing their own fetching. Kept
   deliberately simple (`useState`, no global store) since the app has one
   page and no deep prop-drilling problem yet — the first real complexity
   trigger for reaching for something like Zustand/Redux would be needing
   this state in a second, unrelated part of the tree.
4. **Per-document, not global, chat history.** Messages are keyed by
   `document_id` (`Record<number, ChatMessage[]>`), so switching documents
   shows that document's own conversation instead of a single shared
   thread — this only matters because the backend itself is stateless
   per-query (no server-side conversation memory), so *all* continuity is a
   frontend concern.

## 4. Concrete issues hit while wiring it up

Real problems, in the order they'd actually bite someone doing this for
the first time:

**CORS.** The first fetch from `:3000` to `:8000` fails silently in the
browser console with a CORS error, not a helpful message. Fixed with
`CORSMiddleware` on the backend, allow-listing `http://localhost:3000`
explicitly.
> Gotcha: the allow-list is pinned to Next's *default* dev port. If 3000 is
> taken and Next falls back to 3001, every request breaks with a CORS
> error that has nothing to do with the actual request — easy to lose time
> on if you don't think to check the port first.

**No streaming — long requests need real loading UX, not a spinner.**
`/query` runs 3–5 sequential LLM calls server-side (retrieve → generate →
verify → repair → relevance) before returning anything. Measured 12–90+
seconds on a local model. A plain "await fetch, then render" UI looks
frozen. Built an explicit elapsed-time indicator and per-message loading
state instead of assuming a snappy round trip.

**File uploads are multipart, not JSON.** `POST /documents/upload` takes
`multipart/form-data`; `/query` takes plain JSON. Two different `fetch`
shapes in the same API client — and forgetting to *omit* the
`Content-Type` header on the upload call would break it, since the browser
has to set the multipart boundary itself.

**Empty response bodies break naive JSON parsing.** `DELETE
/documents/{id}` returns `204 No Content` — calling `.json()` on it throws,
since there's no body. The shared `handleResponse` helper special-cases
204 before attempting to parse.

**Inconsistent error response shapes.** A clean `HTTPException` comes back
as `{"detail": "..."}`; a raw 500, a network failure, or the backend being
down entirely might not be JSON at all. `handleResponse` tries to parse
JSON, catches failure, and falls back to `response.statusText`.

**No shared contract between backend and frontend types.** Pydantic
models and the hand-written TypeScript interfaces in `lib/api.ts` are two
independent sources of truth — nothing enforces they stay in sync. When
`RAGResult` gained `metrics` and `rejected` fields on the backend, the
frontend types had to be updated by hand. The real answer at scale is
OpenAPI-client codegen (e.g. `openapi-typescript`); worth naming as a known
gap rather than pretending it isn't one.

**The `NEXT_PUBLIC_` prefix requirement.** Client-side code can only read
env vars prefixed `NEXT_PUBLIC_` — anything else is silently `undefined` in
the browser bundle (while working fine server-side, which makes the bug
extra confusing to track down).

**File inputs can't be set programmatically.** `<input type="file">.value`
can only ever be scripted to `""` — a deliberate browser security
restriction, not a bug. It means upload flows can only be exercised by a
real user gesture or a dedicated browser-automation file-injection API,
which matters for anyone testing this by hand or writing E2E tests later.
The redesigned sidebar adds drag-and-drop as an *additional* real user
gesture path, but doesn't (can't) get around this for scripted testing.

**Stale state across selection changes.** Switching the selected document
without clearing that document's transient UI state would leave the
*previous* document's in-flight loading indicator or error visible against
the newly selected one. Solved by keying all per-document UI state
(messages, in particular) by `document_id` rather than using flat
component state that has to be manually reset on every selection change.

**`document_id` type consistency.** Path params, JSON body fields, and
JS/TS numbers all have to agree it's an integer. A stray string vs. number
mismatch between a delete action and a query body would silently produce a
`422 Unprocessable Entity` from FastAPI's Pydantic validation — a
backend-side error whose actual cause is a frontend typing slip.

## 5. If asked "walk me through connecting this frontend to backend"

Short version to say out loud: *"The backend was built API-first with a
typed contract via Pydantic/OpenAPI, so the frontend work was mostly:
add CORS so the browser would even allow the calls, write a thin typed
client that centralizes error handling and content-type differences
between JSON and multipart endpoints, and model UI state around the fact
that the backend is stateless per-request — so anything that needs to
persist across a session, like chat history, has to live entirely on the
client."*
