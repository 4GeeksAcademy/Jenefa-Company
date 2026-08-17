"use client";

import { FormEvent, useState } from "react";
import { ErrorPanel } from "@/components/ErrorPanel";
import { changePassword } from "@/lib/authApi";
import { toUserFacingMessage, withErrorNumber } from "@/lib/userFacingError";

export default function ChangePasswordPage() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    if (newPassword !== confirmPassword) {
      setError(withErrorNumber("New password and confirmation do not match.", 400));
      return;
    }

    setSubmitting(true);
    try {
      const result = await changePassword(currentPassword, newPassword);
      setSuccess(result.message);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(toUserFacingMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-2xl">
      <section className="border border-border bg-surface px-6 py-8">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">
          Account
        </p>
        <h2 className="mt-2 font-display text-3xl tracking-tight text-foreground">
          Change password
        </h2>
        <p className="mt-3 text-sm leading-6 text-muted">
          Update your staff credentials while signed in. Your current password is
          required.
        </p>

        <form className="mt-6 flex flex-col gap-4" onSubmit={onSubmit}>
          {error ? (
            <ErrorPanel title="Password could not be updated" message={error} />
          ) : null}
          {success ? (
            <div
              role="status"
              className="border border-accent bg-accent-soft px-4 py-3 text-sm text-sidebar"
            >
              {success}
            </div>
          ) : null}
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-foreground">Current password</span>
            <input
              type="password"
              autoComplete="current-password"
              required
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
              className="border border-border px-3 py-2"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-foreground">New password</span>
            <input
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
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
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              className="border border-border px-3 py-2"
            />
          </label>
          <button
            type="submit"
            disabled={submitting}
            className="mt-2 w-fit bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-sidebar-hover disabled:opacity-60"
          >
            {submitting ? "Updating…" : "Update password"}
          </button>
        </form>
      </section>
    </div>
  );
}
