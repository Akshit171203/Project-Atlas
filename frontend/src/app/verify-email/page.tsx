"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { ApiError, verifyEmail } from "@/lib/api";
import { AlertIcon, CheckIcon, SpinnerIcon } from "@/components/icons";

type State =
  | { status: "verifying" }
  | { status: "done"; message: string }
  | { status: "failed"; message: string };

export default function VerifyEmailPage() {
  const [state, setState] = useState<State>({ status: "verifying" });

  // React runs effects twice in development StrictMode. Without this
  // guard the token would be submitted twice, and while the endpoint is
  // idempotent by design, the second call would still race the first.
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    // Read the token from the URL directly rather than through
    // useSearchParams, which would force this page into a Suspense
    // boundary just to read one query parameter.
    const token = new URLSearchParams(window.location.search).get("token");

    // Every state update happens in a promise callback, never in the
    // effect body. Setting state synchronously there triggers a second
    // render pass before the browser paints the first one.
    Promise.resolve()
      .then(() => {
        if (!token) {
          throw new ApiError(
            400,
            "This link is missing its verification token.",
          );
        }
        return verifyEmail(token);
      })
      .then((result) => setState({ status: "done", message: result.message }))
      .catch((err) =>
        setState({
          status: "failed",
          message:
            err instanceof ApiError
              ? err.message
              : "Could not reach the server. Is the backend running on :8000?",
        }),
      );
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-950 px-4 text-neutral-100">
      <div className="w-full max-w-sm text-center">
        {state.status === "verifying" ? (
          <>
            <SpinnerIcon className="mx-auto h-5 w-5 animate-spin text-neutral-700" />
            <p className="mt-4 text-sm text-neutral-500">
              Verifying your email…
            </p>
          </>
        ) : (
          <>
            <div
              className={`mx-auto mb-4 flex h-11 w-11 items-center justify-center rounded-xl border ${
                state.status === "done"
                  ? "border-green-800 bg-green-500/10"
                  : "border-red-900 bg-red-500/10"
              }`}
            >
              {state.status === "done" ? (
                <CheckIcon className="h-5 w-5 text-green-400" />
              ) : (
                <AlertIcon className="h-5 w-5 text-red-400" />
              )}
            </div>

            <h1 className="text-lg font-semibold text-neutral-100">
              {state.status === "done"
                ? "Email verified"
                : "Verification failed"}
            </h1>

            <p className="mt-2 text-sm leading-relaxed text-neutral-500">
              {state.message}
            </p>

            <Link
              href="/"
              className="mt-6 inline-block rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-indigo-500"
            >
              {state.status === "done" ? "Go to sign in" : "Back to sign in"}
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
