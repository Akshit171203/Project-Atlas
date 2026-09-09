"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ApiError,
  askQuestion,
  deleteDocument,
  DocumentRecord,
  listDocuments,
  uploadDocument,
} from "@/lib/api";
import { ChatMessage, ChatPanel } from "@/components/ChatPanel";
import { DocumentSidebar } from "@/components/DocumentSidebar";
import { SessionStats } from "@/components/SessionStats";
import { MenuIcon } from "@/components/icons";

export default function Home() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [documentsError, setDocumentsError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);
  const [messagesByDoc, setMessagesByDoc] = useState<
    Record<number, ChatMessage[]>
  >({});

  async function refreshDocuments() {
    try {
      const docs = await listDocuments();
      setDocuments(docs);
      setDocumentsError(null);
    } catch (err) {
      setDocumentsError(
        err instanceof ApiError
          ? `Failed to load documents: ${err.message}`
          : "Failed to reach the backend. Is it running on :8000?",
      );
    }
  }

  useEffect(() => {
    refreshDocuments();
  }, []);

  async function handleUpload(file: File) {
    setUploading(true);
    setUploadError(null);
    try {
      await uploadDocument(file);
      await refreshDocuments();
    } catch (err) {
      setUploadError(err instanceof ApiError ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(id: number) {
    try {
      await deleteDocument(id);
      if (selectedDocId === id) setSelectedDocId(null);
      setMessagesByDoc((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      await refreshDocuments();
    } catch (err) {
      setDocumentsError(
        err instanceof ApiError ? err.message : "Failed to delete document.",
      );
    }
  }

  async function handleAsk(query: string) {
    if (!selectedDocId) return;
    const docId = selectedDocId;
    const messageId = crypto.randomUUID();

    setMessagesByDoc((prev) => ({
      ...prev,
      [docId]: [
        ...(prev[docId] ?? []),
        { id: messageId, query, status: "loading", askedAt: new Date() },
      ],
    }));

    try {
      const result = await askQuestion(query, docId);
      setMessagesByDoc((prev) => ({
        ...prev,
        [docId]: (prev[docId] ?? []).map((m) =>
          m.id === messageId ? { ...m, status: "done", result } : m,
        ),
      }));
    } catch (err) {
      setMessagesByDoc((prev) => ({
        ...prev,
        [docId]: (prev[docId] ?? []).map((m) =>
          m.id === messageId
            ? {
                ...m,
                status: "error",
                error: err instanceof ApiError ? err.message : "Query failed.",
              }
            : m,
        ),
      }));
    }
  }

  function handleClear() {
    if (!selectedDocId) return;
    setMessagesByDoc((prev) => ({ ...prev, [selectedDocId]: [] }));
  }

  const selectedDoc =
    documents.find((d) => d.id === selectedDocId) ?? null;

  const sessionStats = useMemo(() => {
    const allMessages = Object.values(messagesByDoc).flat();
    const done = allMessages.filter(
      (m) => m.status === "done" && m.result?.metrics,
    );
    return {
      queryCount: allMessages.length,
      totalTokens: done.reduce(
        (sum, m) => sum + (m.result?.metrics?.total_tokens ?? 0),
        0,
      ),
      totalDuration: done.reduce(
        (sum, m) => sum + (m.result?.metrics?.total_duration_seconds ?? 0),
        0,
      ),
    };
  }, [messagesByDoc]);

  return (
    <div className="flex h-screen bg-neutral-950 text-neutral-100">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/60 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <div
        className={`fixed inset-y-0 left-0 z-30 transition-transform md:static md:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <DocumentSidebar
          documents={documents}
          documentsError={documentsError}
          selectedDocId={selectedDocId}
          uploading={uploading}
          uploadError={uploadError}
          onSelect={(id) => {
            setSelectedDocId(id);
            setSidebarOpen(false);
          }}
          onDelete={handleDelete}
          onUpload={handleUpload}
          onClose={() => setSidebarOpen(false)}
        />
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center gap-3 border-b border-neutral-800/80 px-4 py-2.5 md:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="rounded-md p-1.5 text-neutral-400 hover:bg-neutral-900"
          >
            <MenuIcon className="h-5 w-5" />
          </button>
          <span className="text-sm font-medium text-neutral-200">
            Project Atlas
          </span>
        </div>

        {sessionStats.queryCount > 0 && (
          <div className="hidden justify-end border-b border-neutral-800/80 px-6 py-2 md:flex">
            <SessionStats {...sessionStats} />
          </div>
        )}

        <ChatPanel
          document={selectedDoc}
          messages={selectedDocId ? (messagesByDoc[selectedDocId] ?? []) : []}
          onAsk={handleAsk}
          onClear={handleClear}
        />
      </div>
    </div>
  );
}
