"use client";

import { useState } from "react";
import { RAGResult } from "@/lib/api";
import { AlertIcon, CheckIcon, ChevronIcon, CopyIcon } from "./icons";
import { Markdown } from "./Markdown";

export function ResultCard({ result }: { result: RAGResult }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const claimCount = result.verification.verifications.length;
  const supportedCount = result.verification.verifications.filter(
    (v) => v.supported,
  ).length;

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(result.answer);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard API can be unavailable (permissions, insecure context)
      // — silently do nothing rather than throw in the UI.
    }
  }

  return (
    <div className="group/card animate-fade-in-up space-y-3 rounded-2xl rounded-bl-md border border-neutral-800 bg-neutral-900/60 p-4">
      {result.rejected && (
        <div className="flex items-start gap-2 rounded-lg border border-amber-900/60 bg-amber-500/10 px-3 py-2 text-xs text-amber-300">
          <AlertIcon className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <span>
            The generated answer failed the relevance check and was
            withheld.
          </span>
        </div>
      )}

      <div className="relative">
        <Markdown>{result.answer}</Markdown>
        <button
          onClick={handleCopy}
          title="Copy answer"
          className="absolute -right-1 -top-1 rounded-md p-1.5 text-neutral-600 opacity-0 transition-opacity hover:bg-neutral-800 hover:text-neutral-300 group-hover/card:opacity-100"
        >
          {copied ? (
            <CheckIcon className="h-3.5 w-3.5 text-green-400" />
          ) : (
            <CopyIcon className="h-3.5 w-3.5" />
          )}
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        <Badge
          tone={result.answerable ? "neutral" : "red"}
          label={result.answerable ? "answerable" : "not answerable"}
        />
        {result.repaired && <Badge tone="amber" label="repaired" />}
        {result.relevance && (
          <Badge
            tone={result.relevance.relevant ? "green" : "red"}
            label={`relevance ${result.relevance.score.toFixed(2)}`}
          />
        )}
        {result.metrics && (
          <span className="ml-auto text-[11px] text-neutral-600">
            {result.metrics.llm_call_count} LLM calls ·{" "}
            {result.metrics.total_duration_seconds.toFixed(1)}s
            {result.metrics.total_tokens
              ? ` · ${result.metrics.total_tokens} tokens`
              : ""}
          </span>
        )}
      </div>

      {claimCount > 0 && (
        <div className="border-t border-neutral-800 pt-2.5">
          <button
            onClick={() => setExpanded((v) => !v)}
            className="flex items-center gap-1.5 text-xs font-medium text-neutral-400 hover:text-neutral-200"
          >
            <ChevronIcon
              className={`h-3.5 w-3.5 transition-transform ${
                expanded ? "rotate-180" : ""
              }`}
            />
            Citation verification
            <span className="text-neutral-600">
              ({supportedCount}/{claimCount} supported)
            </span>
          </button>

          {expanded && (
            <ul className="mt-2.5 space-y-1.5">
              {result.verification.verifications.map((v, i) => (
                <li
                  key={i}
                  className={`rounded-lg border px-2.5 py-2 text-[12px] leading-snug ${
                    v.supported
                      ? "border-green-900/50 bg-green-500/5"
                      : "border-red-900/50 bg-red-500/5"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <span
                      className={
                        v.supported ? "text-green-200" : "text-red-200"
                      }
                    >
                      <span className="font-medium text-neutral-400">
                        [{v.source_id}]
                      </span>{" "}
                      {v.claim}
                    </span>
                    <span className="shrink-0 text-neutral-500">
                      {v.label}
                    </span>
                  </div>
                  <ScoreBar score={v.score} supported={v.supported} />
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

function ScoreBar({
  score,
  supported,
}: {
  score: number;
  supported: boolean;
}) {
  const pct = Math.max(2, Math.min(100, score * 100));
  return (
    <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-neutral-800">
      <div
        className={`h-full rounded-full transition-all ${
          supported ? "bg-green-500" : "bg-red-500"
        }`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

function Badge({
  label,
  tone,
}: {
  label: string;
  tone: "neutral" | "green" | "red" | "amber";
}) {
  const tones: Record<string, string> = {
    neutral: "border-neutral-700 text-neutral-400",
    green: "border-green-800 bg-green-500/10 text-green-400",
    red: "border-red-800 bg-red-500/10 text-red-400",
    amber: "border-amber-800 bg-amber-500/10 text-amber-400",
  };
  return (
    <span
      className={`rounded-full border px-2 py-0.5 text-[11px] font-medium ${tones[tone]}`}
    >
      {label}
    </span>
  );
}
