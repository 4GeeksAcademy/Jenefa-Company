"use client";

import Link from "next/link";
import { FormEvent, Suspense, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AuthShell } from "@/components/AuthShell";
import { ApiRequestError } from "@/lib/api";
import { resetPassword } from "@/lib/authApi";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = useMemo(() => searchParams.get("token")?.trim() ?? "", [searchParams]);

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [tokenFailed, setTokenFailed] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setTokenFailed(false);

    if (!token) {
      setTokenFailed(true);
      setError("This reset link is missing a token. Request a new one.");
      return;
    }
    if (password !== confirm) {
      setError("New password and confirmation do not match.");
      return;
    }

    setSubmitting(true);
    try {
      await resetPassword(token, password);
      router.replace("/login");
    } catch (err) {
      const message =
        err instanceof ApiRequestError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Unable to reset password.";
      setError(message);
      setTokenFailed(true);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={onSubmit}>
      {error ? (
        <div
          role="alert"
          className="border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-900"
        >
          <p>{error}</p>
          {tokenFailed ? (
            <p className="mt-2">
              <Link
                href="/forgot-password"
                className="font-medium text-accent underline-offset-2 hover:underline"
              >
                Request a new reset link
              </Link>
            </p>
          ) : null}
        </div>
      ) : null}
      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-foreground">New password</span>
        <input
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="border border-border px-3 py-2"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-foreground">Confirm new password</span>
        <input
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          value={confirm}
          onChange={(event) => setConfirm(event.target.value)}
          className="border border-border px-3 py-2"
        />
      </label>
      <button
        type="submit"
        disabled={submitting}
        className="mt-2 bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-sidebar-hover disabled:opacity-60"
      >
        {submitting ? "Updating…" : "Update password"}
      </button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <AuthShell
      title="Reset password"
      subtitle="Choose a new password using the link from your recovery email."
    >
      <Suspense
        fallback={
          <p className="text-sm text-muted">Loading reset form…</p>
        }
      >
        <ResetPasswordForm />
      </Suspense>
    </AuthShell>
  );
}
