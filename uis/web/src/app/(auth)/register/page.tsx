"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthShell } from "@/components/AuthShell";
import { ErrorPanel } from "@/components/ErrorPanel";
import { ApiRequestError } from "@/lib/api";
import { registerAndLogin } from "@/lib/authApi";
import { toUserFacingMessage } from "@/lib/userFacingError";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setFieldErrors({});
    setSubmitting(true);
    try {
      await registerAndLogin({ email, password, name, phone, address });
      router.replace("/");
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(toUserFacingMessage(err));
        setFieldErrors(
          Object.fromEntries(err.fieldErrors.map((item) => [item.field, item.message]))
        );
      } else {
        setError(toUserFacingMessage(err));
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      title="Register"
      subtitle="Create a staff account, then continue straight into the workspace."
    >
      <form className="flex flex-col gap-4" onSubmit={onSubmit}>
        {error ? (
          <ErrorPanel title="Account could not be created" message={error} />
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
          {fieldErrors.email ? (
            <span className="text-xs text-red-800">{fieldErrors.email}</span>
          ) : null}
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-foreground">Password</span>
          <input
            type="password"
            autoComplete="new-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="border border-border px-3 py-2"
          />
          {fieldErrors.password ? (
            <span className="text-xs text-red-800">{fieldErrors.password}</span>
          ) : null}
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-foreground">Name (optional)</span>
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="border border-border px-3 py-2"
          />
          {fieldErrors.name ? (
            <span className="text-xs text-red-800">{fieldErrors.name}</span>
          ) : null}
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-foreground">Phone (optional)</span>
          <input
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
            className="border border-border px-3 py-2"
          />
          {fieldErrors.phone ? (
            <span className="text-xs text-red-800">{fieldErrors.phone}</span>
          ) : null}
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-foreground">Address (optional)</span>
          <input
            value={address}
            onChange={(event) => setAddress(event.target.value)}
            className="border border-border px-3 py-2"
          />
          {fieldErrors.address ? (
            <span className="text-xs text-red-800">{fieldErrors.address}</span>
          ) : null}
        </label>
        <button
          type="submit"
          disabled={submitting}
          className="mt-2 bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-sidebar-hover disabled:opacity-60"
        >
          {submitting ? "Creating account…" : "Create account"}
        </button>
      </form>
    </AuthShell>
  );
}
