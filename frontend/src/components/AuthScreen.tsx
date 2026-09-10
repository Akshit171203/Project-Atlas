"use client";

import { useState } from "react";
import { ApiError, resendVerification } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { AlertIcon, CheckIcon, LockIcon, SpinnerIcon } from "./icons";

type Mode = "login" | "signup";

export function AuthScreen() {
  const { login, signup } = useAuth();

  const [mode, setMode] = useState<Mode>("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Set when the account exists but its address is unconfirmed - either
  // straight after signup, or when login comes back 403 for an
  // unverified account. Both land on the same "check your inbox" panel.
  const [pendingEmail, setPendingEmail] = useState<string | null>(null);

  const isSignup = mode === "signup";

  if (pendingEmail) {
    return (
      <VerificationPending
        email={pendingEmail}
        onBack={() => {
          setPendingEmail(null);
          switchMode("login");
        }}
      />
    );
  }

  function switchMode(next: Mode) {
    setMode(next);
    // Carry the email across but never the password — a failed login
    // followed by a switch to signup shouldn't silently reuse a
    // half-typed credential.
    setPassword("");
    setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (submitting) return;

    setSubmitting(true);
    setError(null);

    try {
      if (isSignup) {
        const signedIn = await signup(name.trim(), email.trim(), password);
        if (!signedIn) {
          setPendingEmail(email.trim());
          setSubmitting(false);
          return;
        }
      } else {
        await login(email.trim(), password);
      }
      // On success the provider sets the user and this screen unmounts.
    } catch (err) {
      if (err instanceof ApiError) {
        // 403 on login means the password was right but the address is
        // unconfirmed - send them to the resend panel rather than showing
        // a dead-end error.
        if (err.status === 403) {
          setPendingEmail(email.trim());
          setSubmitting(false);
          return;
        }
        // 422 is Pydantic rejecting the payload shape; its raw detail is a
        // nested array that means nothing to a person.
        setError(
          err.status === 422
            ? "Please enter a valid email and a password of at least 8 characters."
            : err.message,
        );
      } else {
        setError("Could not reach the server. Is the backend running on :8000?");
      }
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-950 px-4 text-neutral-100">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-600 text-lg font-semibold text-white">
            A
          </div>
          <h1 className="text-lg font-semibold text-neutral-100">
            Project Atlas
          </h1>
          <p className="mt-1 text-sm text-neutral-500">
            {isSignup
              ? "Create an account to upload and query documents."
              : "Sign in to your documents."}
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-3 rounded-2xl border border-neutral-800 bg-neutral-900/50 p-5"
        >
          {isSignup && (
            <Field
              label="Name"
              value={name}
              onChange={setName}
              type="text"
              autoComplete="name"
              placeholder="Akshit Gupta"
              required
              disabled={submitting}
            />
          )}

          <Field
            label="Email"
            value={email}
            onChange={setEmail}
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            required
            disabled={submitting}
          />

          <Field
            label="Password"
            value={password}
            onChange={setPassword}
            type="password"
            // Tells a password manager whether to offer a saved credential
            // or to generate a new one.
            autoComplete={isSignup ? "new-password" : "current-password"}
            placeholder={isSignup ? "At least 8 characters" : "••••••••"}
            required
            minLength={isSignup ? 8 : undefined}
            disabled={submitting}
          />

          {error && (
            <div
              role="alert"
              className="flex items-start gap-2 rounded-lg border border-red-900/60 bg-red-500/10 px-3 py-2 text-xs text-red-300"
            >
              <AlertIcon className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting && <SpinnerIcon className="h-3.5 w-3.5 animate-spin" />}
            {submitting
              ? isSignup
                ? "Creating account…"
                : "Signing in…"
              : isSignup
                ? "Create account"
                : "Sign in"}
          </button>

          <p className="pt-1 text-center text-xs text-neutral-500">
            {isSignup ? "Already have an account?" : "No account yet?"}{" "}
            <button
              type="button"
              onClick={() => switchMode(isSignup ? "login" : "signup")}
              disabled={submitting}
              className="font-medium text-indigo-400 hover:text-indigo-300 disabled:opacity-60"
            >
              {isSignup ? "Sign in" : "Create one"}
            </button>
          </p>
        </form>

        <p className="mt-4 flex items-center justify-center gap-1.5 text-[11px] text-neutral-600">
          <LockIcon className="h-3 w-3" />
          Your documents are visible only to you.
        </p>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  ...props
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
} & Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange" | "value">) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-medium text-neutral-400">
        {label}
      </span>
      <input
        {...props}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm text-neutral-100 placeholder-neutral-700 outline-none transition-colors focus:border-indigo-600 disabled:opacity-60"
      />
    </label>
  );
}

function VerificationPending({
  email,
  onBack,
}: {
  email: string;
  onBack: () => void;
}) {
  const [sending, setSending] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  async function handleResend() {
    setSending(true);
    setNotice(null);
    try {
      const result = await resendVerification(email);
      setNotice(result.message);
    } catch {
      setNotice("Could not reach the server. Try again in a moment.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-950 px-4 text-neutral-100">
      <div className="w-full max-w-sm text-center">
        <div className="mx-auto mb-4 flex h-11 w-11 items-center justify-center rounded-xl border border-indigo-800 bg-indigo-500/10">
          <CheckIcon className="h-5 w-5 text-indigo-400" />
        </div>

        <h1 className="text-lg font-semibold text-neutral-100">
          Check your email
        </h1>

        <p className="mt-2 text-sm leading-relaxed text-neutral-500">
          We sent a verification link to{" "}
          <span className="text-neutral-300">{email}</span>. Open it to
          activate your account, then sign in.
        </p>

        <div className="mt-6 space-y-3 rounded-2xl border border-neutral-800 bg-neutral-900/50 p-5">
          <button
            onClick={handleResend}
            disabled={sending}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-neutral-700 px-4 py-2.5 text-sm font-medium text-neutral-200 transition-colors hover:bg-neutral-800 disabled:opacity-60"
          >
            {sending && <SpinnerIcon className="h-3.5 w-3.5 animate-spin" />}
            {sending ? "Sending…" : "Resend verification email"}
          </button>

          {notice && (
            <p className="text-xs leading-relaxed text-neutral-500">{notice}</p>
          )}

          <button
            onClick={onBack}
            className="text-xs font-medium text-indigo-400 hover:text-indigo-300"
          >
            Back to sign in
          </button>
        </div>

        <p className="mt-4 text-[11px] leading-relaxed text-neutral-600">
          No mail server configured? The link is printed in the backend
          console.
        </p>
      </div>
    </div>
  );
}
