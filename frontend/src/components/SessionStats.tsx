"use client";

import { ActivityIcon } from "./icons";

export function SessionStats({
  queryCount,
  totalTokens,
  totalDuration,
}: {
  queryCount: number;
  totalTokens: number;
  totalDuration: number;
}) {
  if (queryCount === 0) return null;

  return (
    <div className="flex items-center gap-3 rounded-lg border border-neutral-800/80 bg-neutral-900/40 px-3 py-1.5 text-[11px] text-neutral-500">
      <ActivityIcon className="h-3.5 w-3.5 text-neutral-600" />
      <span>
        {queryCount} quer{queryCount === 1 ? "y" : "ies"} this session
      </span>
      <span className="text-neutral-700">·</span>
      <span>{totalTokens.toLocaleString()} tokens</span>
      <span className="text-neutral-700">·</span>
      <span>{totalDuration.toFixed(0)}s total</span>
    </div>
  );
}
