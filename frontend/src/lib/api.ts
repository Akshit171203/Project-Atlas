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

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
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

export async function listDocuments(): Promise<DocumentRecord[]> {
  const response = await fetch(`${API_URL}/documents`);
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
    method: "POST",
    body: formData,
  });

  return handleResponse(response);
}

export async function deleteDocument(documentId: number): Promise<void> {
  const response = await fetch(`${API_URL}/documents/${documentId}`, {
    method: "DELETE",
  });
  return handleResponse<void>(response);
}

export async function askQuestion(
  query: string,
  documentId: number,
): Promise<RAGResult> {
  const response = await fetch(`${API_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, document_id: documentId }),
  });

  return handleResponse<RAGResult>(response);
}
