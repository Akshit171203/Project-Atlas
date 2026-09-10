"use client";

import { useRef, useState } from "react";
import { DocumentRecord } from "@/lib/api";
import { relativeTime } from "@/lib/format";
import { useAuth } from "@/lib/auth";
import {
  FileIcon,
  LogOutIcon,
  SpinnerIcon,
  TrashIcon,
  UploadIcon,
  XIcon,
} from "./icons";

export function DocumentSidebar({
  documents,
  documentsError,
  selectedDocId,
  uploading,
  uploadError,
  onSelect,
  onDelete,
  onUpload,
  onClose,
}: {
  documents: DocumentRecord[];
  documentsError: string | null;
  selectedDocId: number | null;
  uploading: boolean;
  uploadError: string | null;
  onSelect: (id: number) => void;
  onDelete: (id: number) => void;
  onUpload: (file: File) => void;
  onClose?: () => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function pickFile() {
    inputRef.current?.click();
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) onUpload(file);
  }

  return (
    <aside className="flex h-full w-80 shrink-0 flex-col border-r border-neutral-800/80 bg-neutral-950/60">
      <div className="flex items-center justify-between border-b border-neutral-800/80 px-5 py-5">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600 text-sm font-semibold text-white">
            A
          </div>
          <div>
            <h1 className="text-sm font-semibold text-neutral-100">
              Project Atlas
            </h1>
            <p className="text-xs text-neutral-500">RAG document Q&amp;A</p>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-neutral-500 hover:bg-neutral-900 hover:text-neutral-300 md:hidden"
          >
            <XIcon className="h-4 w-4" />
          </button>
        )}
      </div>

      <div className="px-5 py-4">
        <button
          onClick={pickFile}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          disabled={uploading}
          className={`flex w-full flex-col items-center gap-1.5 rounded-xl border border-dashed px-4 py-5 text-center transition-colors disabled:opacity-60 ${
            dragging
              ? "border-indigo-500 bg-indigo-500/10"
              : "border-neutral-700 hover:border-neutral-600 hover:bg-neutral-900"
          }`}
        >
          {uploading ? (
            <SpinnerIcon className="h-5 w-5 text-indigo-400" />
          ) : (
            <UploadIcon className="h-5 w-5 text-neutral-500" />
          )}
          <span className="text-xs font-medium text-neutral-300">
            {uploading ? "Uploading…" : "Drop a PDF or click to upload"}
          </span>
        </button>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onUpload(file);
            e.target.value = "";
          }}
        />
        {uploadError && (
          <p className="mt-2 text-xs text-red-400">{uploadError}</p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-3 pb-4">
        <div className="flex items-center justify-between px-2 pb-2">
          <h2 className="text-[11px] font-medium uppercase tracking-wide text-neutral-600">
            Documents
          </h2>
          {documents.length > 0 && (
            <span className="text-[11px] text-neutral-700">
              {documents.length}
            </span>
          )}
        </div>

        {documentsError && (
          <p className="px-2 text-xs text-red-400">{documentsError}</p>
        )}

        {!documentsError && documents.length === 0 && (
          <p className="px-2 text-xs text-neutral-600">
            No documents yet — upload a PDF to get started.
          </p>
        )}

        <ul className="space-y-0.5">
          {documents.map((doc) => {
            const active = selectedDocId === doc.id;
            return (
              <li key={doc.id}>
                <div
                  className={`group flex items-center gap-2 rounded-lg px-2 py-2 text-sm transition-colors ${
                    active
                      ? "bg-indigo-500/15 text-indigo-300"
                      : "text-neutral-300 hover:bg-neutral-900"
                  }`}
                >
                  <button
                    onClick={() => onSelect(doc.id)}
                    className="flex min-w-0 flex-1 items-center gap-2 text-left"
                  >
                    <FileIcon
                      className={`h-4 w-4 shrink-0 ${
                        active ? "text-indigo-400" : "text-neutral-600"
                      }`}
                    />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate" title={doc.filename}>
                        {doc.filename}
                      </span>
                      <span className="block text-[11px] text-neutral-600">
                        {doc.total_pages} page{doc.total_pages === 1 ? "" : "s"}
                        {" · "}
                        {relativeTime(doc.created_at)}
                      </span>
                    </span>
                  </button>
                  <button
                    onClick={() => onDelete(doc.id)}
                    title="Delete document"
                    className="shrink-0 rounded-md p-1 text-neutral-700 opacity-0 transition-opacity hover:bg-red-500/10 hover:text-red-400 group-hover:opacity-100"
                  >
                    <TrashIcon className="h-3.5 w-3.5" />
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      </div>

      <AccountFooter />
    </aside>
  );
}

function AccountFooter() {
  const { user, logout } = useAuth();
  const [signingOut, setSigningOut] = useState(false);

  if (!user) return null;

  async function handleLogout() {
    setSigningOut(true);
    try {
      await logout();
    } finally {
      // No need to clear the flag on success — logging out unmounts this
      // whole tree.
      setSigningOut(false);
    }
  }

  const initial = (user.name || user.email).charAt(0).toUpperCase();

  return (
    <div className="flex items-center gap-2.5 border-t border-neutral-800/80 px-4 py-3">
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-neutral-800 text-xs font-semibold text-neutral-300">
        {initial}
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <span
            className="truncate text-xs font-medium text-neutral-200"
            title={user.name}
          >
            {user.name}
          </span>
          {user.role === "ADMIN" && (
            <span className="shrink-0 rounded-full border border-indigo-800 bg-indigo-500/10 px-1.5 py-px text-[10px] font-medium text-indigo-400">
              admin
            </span>
          )}
        </div>
        <span className="block truncate text-[11px] text-neutral-600" title={user.email}>
          {user.email}
        </span>
      </div>

      <button
        onClick={handleLogout}
        disabled={signingOut}
        title="Sign out"
        className="shrink-0 rounded-md p-1.5 text-neutral-600 transition-colors hover:bg-neutral-900 hover:text-neutral-300 disabled:opacity-50"
      >
        {signingOut ? (
          <SpinnerIcon className="h-3.5 w-3.5 animate-spin" />
        ) : (
          <LogOutIcon className="h-3.5 w-3.5" />
        )}
      </button>
    </div>
  );
}
