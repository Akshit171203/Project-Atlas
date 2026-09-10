const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface DocumentRecord {
  id: number;
  filename: string;
  total_pages: number;
  created_at: string;
}

export interface CitationVerification {
  claim: string;
  source_id: string;
  label: string;
  score: number;
  supported: boolean;
  reason: string;
}

export interface CitationVerificationResult {
  verifications: CitationVerification[];
}

export interface AnswerRelevanceResult {
  relevant: boolean;
  score: number;
  reason: string;
}

export interface QueryMetrics {
  llm_call_count: number;
  total_duration_seconds: number;
  total_tokens: number | null;
}

export interface RAGResult {
  answer: string;
  verification: CitationVerificationResult;
  repaired: boolean;
  initial_answer: string | null;
  initial_verification: CitationVerificationResult | null;
  answerable: boolean;
  retrieval_chunk_ids: number[];
  relevance: AnswerRelevanceResult | null;
  metrics: QueryMetrics | null;
  rejected: boolean;
}

export type UserRole = "ADMIN" | "USER";

export interface UserRecord {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  verified: boolean;
  created_at: string;
}

export interface SignupResponse {
  user: UserRecord;
  /** False when the account must verify its email before signing in. */
  authenticated: boolean;
  message: string;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

// The session cookie expires after JWT_EXPIRE_MINUTES, which can happen
// mid-session while the tab is open. Rather than let every caller handle
// that separately, the auth provider registers here and gets told once,
// from the single place every response already passes through.
let onUnauthorized: (() => void) | null = null;

export function setUnauthorizedHandler(handler: (() => void) | null) {
  onUnauthorized = handler;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.status === 401) {
    onUnauthorized?.();
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // Non-JSON error body (e.g. a raw 500 with no payload) — fall
      // back to statusText rather than throwing a parse error here.
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

// Without credentials: "include" the browser never attaches the session
// cookie to a cross-origin request (:3000 -> :8000), so every call would
// come back 401 even with a perfectly valid cookie set. It is required on
// every request, not just the auth ones.
const withCredentials: RequestInit = { credentials: "include" };

export async function listDocuments(): Promise<DocumentRecord[]> {
  const response = await fetch(`${API_URL}/documents`, withCredentials);
  return handleResponse<DocumentRecord[]>(response);
}

export async function uploadDocument(file: File): Promise<{
  document_id: number;
  filename: string;
  pages: number;
  chunks: number;
  embeddings: number;
}> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/documents/upload`, {
    ...withCredentials,
    method: "POST",
    // Content-Type is deliberately not set: the browser has to generate the
    // multipart boundary itself, and setting it by hand breaks the upload.
    body: formData,
  });

  return handleResponse(response);
}

export async function deleteDocument(documentId: number): Promise<void> {
  const response = await fetch(`${API_URL}/documents/${documentId}`, {
    ...withCredentials,
    method: "DELETE",
  });
  return handleResponse<void>(response);
}

export async function askQuestion(
  query: string,
  documentId: number,
): Promise<RAGResult> {
  const response = await fetch(`${API_URL}/query`, {
    ...withCredentials,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, document_id: documentId }),
  });

  return handleResponse<RAGResult>(response);
}

// --- Auth -----------------------------------------------------------------

export async function signup(
  name: string,
  email: string,
  password: string,
): Promise<SignupResponse> {
  const response = await fetch(`${API_URL}/auth/signup`, {
    ...withCredentials,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password }),
  });
  return handleResponse<SignupResponse>(response);
}

export async function verifyEmail(token: string): Promise<{ message: string }> {
  const response = await fetch(
    `${API_URL}/auth/verify-email?token=${encodeURIComponent(token)}`,
    withCredentials,
  );
  return handleResponse<{ message: string }>(response);
}

export async function resendVerification(
  email: string,
): Promise<{ message: string }> {
  const response = await fetch(`${API_URL}/auth/resend-verification`, {
    ...withCredentials,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  return handleResponse<{ message: string }>(response);
}

export async function login(
  email: string,
  password: string,
): Promise<UserRecord> {
  const response = await fetch(`${API_URL}/auth/login`, {
    ...withCredentials,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return handleResponse<UserRecord>(response);
}

export async function logout(): Promise<void> {
  const response = await fetch(`${API_URL}/auth/logout`, {
    ...withCredentials,
    method: "POST",
  });
  return handleResponse<void>(response);
}

export async function getMe(): Promise<UserRecord> {
  const response = await fetch(`${API_URL}/auth/me`, withCredentials);
  return handleResponse<UserRecord>(response);
}
