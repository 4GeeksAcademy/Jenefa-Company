"use client";

import { FormEvent, useState } from "react";
import { AuthShell } from "@/components/AuthShell";
import { ErrorPanel } from "@/components/ErrorPanel";
import { requestPasswordReset } from "@/lib/authApi";
import { toUserFacingMessage } from "@/lib/userFacingError";

const CONFIRMATION =
  "If that address is registered, you'll receive a link shortly";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await requestPasswordReset(email);
      setSubmitted(true);
    } catch (err) {
      setError(toUserFacingMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      title="Forgot password"
      subtitle="Enter your staff email. We only send a reset link when the address is registered."
    >
      {submitted ? (
        <p role="status" className="border border-accent bg-accent-soft px-3 py-3 text-sm text-sidebar">
          {CONFIRMATION}
        </p>
      ) : (
        <form className="flex flex-col gap-4" onSubmit={onSubmit}>
          {error ? (
            <ErrorPanel title="Reset request could not be sent" message={error} />
          ) : null}
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-foreground">Email</span>
            <input
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="border border-border px-3 py-2"
              disabled={submitting}
            />
          </label>
          <button
            type="submit"
            disabled={submitting}
            className="mt-2 bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-sidebar-hover disabled:opacity-60"
          >
            {submitting ? "Sending…" : "Send reset link"}
          </button>
        </form>
      )}
    </AuthShell>
  );
}
