"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AuthShell } from "@/components/AuthShell";
import { ErrorPanel } from "@/components/ErrorPanel";
import { loginAndStore } from "@/lib/authApi";
import { toUserFacingMessage } from "@/lib/userFacingError";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await loginAndStore(email, password);
      router.replace("/");
    } catch (err) {
      setError(toUserFacingMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      title="Sign in"
      subtitle="Staff credentials for the HealthCore operations workspace."
    >
      <form className="flex flex-col gap-4" onSubmit={onSubmit}>
        {error ? (
          <ErrorPanel title="Sign-in could not be completed" message={error} />
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
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-foreground">Password</span>
          <input
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="border border-border px-3 py-2"
          />
        </label>
        <p className="text-sm">
          <Link
            href="/forgot-password"
            className="text-accent underline-offset-2 hover:underline"
          >
            Forgot your password?
          </Link>
        </p>
        <button
          type="submit"
          disabled={submitting}
          className="mt-2 bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-sidebar-hover disabled:opacity-60"
        >
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </AuthShell>
  );
}
