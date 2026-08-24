"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { loginAndStore } from "@/lib/authApi";
import { toUserFacingMessage } from "@/lib/userFacingError";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setBusy(true);
    setError(null);
    try {
      await loginAndStore(String(data.get("email") || ""), String(data.get("password") || ""));
      router.push("/inventory");
    } catch (err: unknown) {
      setError(toUserFacingMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-md">
      <section className="rounded-lg border border-border bg-surface px-6 py-8">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">
          Staff access
        </p>
        <h2 className="mt-2 font-display text-3xl tracking-tight text-foreground">Sign in</h2>
        <p className="mt-3 text-sm leading-6 text-muted">
          Clinic operator credentials are required for inventory and other
          restricted ledgers.
        </p>
        <form onSubmit={(event) => void onSubmit(event)} className="mt-6 flex flex-col gap-4">
          <label className="block text-xs font-semibold uppercase tracking-[0.12em] text-muted">
            Email
            <input
              className="mt-1 w-full border border-border bg-background px-3 py-2 text-sm"
              name="email"
              type="email"
              autoComplete="username"
              required
            />
          </label>
          <label className="block text-xs font-semibold uppercase tracking-[0.12em] text-muted">
            Password
            <input
              className="mt-1 w-full border border-border bg-background px-3 py-2 text-sm"
              name="password"
              type="password"
              autoComplete="current-password"
              required
            />
          </label>
          {error ? (
            <p role="alert" className="text-sm text-red-800">
              {error}
            </p>
          ) : null}
          <button
            type="submit"
            disabled={busy}
            className="bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-sidebar-hover disabled:opacity-60"
          >
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </section>
    </div>
  );
}
