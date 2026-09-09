"use client";

import { useEffect, useRef, useState } from "react";
import { DocumentRecord, RAGResult } from "@/lib/api";
import { clockTime, relativeTime } from "@/lib/format";
import {
  AlertIcon,
  BroomIcon,
  FileIcon,
  SendIcon,
  SparkleIcon,
} from "./icons";
import { ResultCard } from "./ResultCard";

export interface ChatMessage {
  id: string;
  query: string;
  status: "loading" | "done" | "error";
  result?: RAGResult;
  error?: string;
  askedAt: Date;
}

const SUGGESTIONS = [
  "Summarize the key point in one sentence",
  "What's the main takeaway here?",
  "Give me a specific fact from this document",
];

export function ChatPanel({
  document,
  messages,
  onAsk,
  onClear,
}: {
  document: DocumentRecord | null;
  messages: ChatMessage[];
  onAsk: (query: string) => void;
  onClear: () => void;
}) {
  const [query, setQuery] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const asking = messages.some((m) => m.status === "loading");

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, [document]);

  function submit(text: string) {
    if (!text.trim() || asking) return;
    onAsk(text.trim());
    setQuery("");
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    submit(query);
  }

  if (!document) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-2 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-neutral-800 bg-neutral-900">
          <FileIcon className="h-5 w-5 text-neutral-600" />
        </div>
        <p className="max-w-xs text-sm text-neutral-500">
          Select a document on the left to ask questions about it.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-neutral-800/80 px-6 py-4">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-neutral-200">
            {document.filename}
          </p>
          <p className="text-xs text-neutral-600">
            {document.total_pages} page{document.total_pages === 1 ? "" : "s"}
            {" · "}
            uploaded {relativeTime(document.created_at)}
          </p>
        </div>
        {messages.length > 0 && (
          <button
            onClick={onClear}
            title="Clear conversation"
            className="flex shrink-0 items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs text-neutral-500 transition-colors hover:bg-neutral-900 hover:text-neutral-300"
          >
            <BroomIcon className="h-3.5 w-3.5" />
            Clear
          </button>
        )}
      </div>

      <div
        ref={scrollRef}
        className="flex-1 space-y-5 overflow-y-auto px-6 py-5"
      >
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
            <SparkleIcon className="h-5 w-5 text-neutral-700" />
            <p className="max-w-sm text-sm text-neutral-600">
              Ask anything about this document — answers are grounded and
              cited, or refused if the source doesn&apos;t cover it.
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => submit(s)}
                  className="rounded-full border border-neutral-800 px-3 py-1.5 text-xs text-neutral-400 transition-colors hover:border-neutral-700 hover:bg-neutral-900 hover:text-neutral-200"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className="space-y-2.5">
            <div className="flex flex-col items-end gap-1">
              <div className="max-w-[80%] rounded-2xl rounded-br-md bg-indigo-600 px-3.5 py-2 text-[13.5px] text-white">
                {message.query}
              </div>
              <span className="text-[10px] text-neutral-700">
                {clockTime(message.askedAt)}
              </span>
            </div>

            {message.status === "loading" && <LoadingBubble />}

            {message.status === "error" && (
              <div className="flex animate-fade-in-up items-start gap-2 rounded-2xl rounded-bl-md border border-red-900/60 bg-red-500/10 px-3.5 py-2.5 text-xs text-red-300">
                <AlertIcon className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                <span>{message.error}</span>
              </div>
            )}

            {message.status === "done" && message.result && (
              <ResultCard result={message.result} />
            )}
          </div>
        ))}
      </div>

      <form
        onSubmit={handleSubmit}
        className="flex gap-2 border-t border-neutral-800/80 px-6 py-4"
      >
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question about this document…"
          disabled={asking}
          className="flex-1 rounded-xl border border-neutral-800 bg-neutral-900 px-3.5 py-2.5 text-sm text-neutral-100 outline-none transition-colors placeholder:text-neutral-600 focus:border-indigo-500 disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={asking || !query.trim()}
          className="flex items-center justify-center rounded-xl bg-indigo-600 px-4 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
        >
          <SendIcon className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}

function LoadingBubble() {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const interval = setInterval(() => {
      setElapsed(Math.round((Date.now() - start) / 1000));
    }, 500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex animate-fade-in-up items-center gap-2.5 rounded-2xl rounded-bl-md border border-neutral-800 bg-neutral-900/60 px-3.5 py-2.5 text-xs text-neutral-500">
      <span className="flex gap-1">
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-indigo-400 [animation-delay:-0.3s]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-indigo-400 [animation-delay:-0.15s]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-indigo-400" />
      </span>
      <span>Retrieving → generating → verifying… {elapsed}s</span>
    </div>
  );
}
