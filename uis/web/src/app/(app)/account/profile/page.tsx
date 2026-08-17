"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  fetchMe,
  fetchMyProfile,
  updateMyProfile,
  type MeResponse,
  type Profile,
} from "@/lib/authApi";
import { ErrorPanel } from "@/components/ErrorPanel";
import { logoutAndRedirect } from "@/lib/authStorage";
import { toUserFacingMessage } from "@/lib/userFacingError";

export default function ProfilePage() {
  const [me, setMe] = useState<MeResponse | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const load = async (ignoreIfCancelled?: () => boolean) => {
    setError(null);
    setLoading(true);
    try {
      const [mePayload, profilePayload] = await Promise.all([fetchMe(), fetchMyProfile()]);
      if (ignoreIfCancelled?.()) return;
      setMe(mePayload);
      setProfile(profilePayload);
      setName(profilePayload?.name ?? "");
      setPhone(profilePayload?.phone ?? "");
      setAddress(profilePayload?.address ?? "");
    } catch (err) {
      if (ignoreIfCancelled?.()) return;
      setError(toUserFacingMessage(err));
    } finally {
      if (!ignoreIfCancelled?.()) setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    void load(() => cancelled);
    return () => {
      cancelled = true;
    };
    // Initial session load only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSaved(false);
    setSaving(true);
    try {
      const updated = await updateMyProfile({ name, phone, address });
      setProfile(updated);
      setSaved(true);
    } catch (err) {
      setError(toUserFacingMessage(err));
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="loading-state text-sm text-muted">
        Verifying session token safety layer...
      </div>
    );
  }

  if (!me) {
    return (
      <div className="mx-auto w-full max-w-2xl">
        <ErrorPanel
          title="Profile could not be loaded"
          message={error ?? "We couldn't complete that request. Please try again."}
          onRetry={() => void load()}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-2xl">
      <section className="border border-border bg-surface px-6 py-8">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">
          Account
        </p>
        <h2 className="mt-2 font-display text-3xl tracking-tight text-foreground">
          Profile
        </h2>
        <p className="mt-3 text-sm leading-6 text-muted">
          Email is stored on the User record. Name and contact fields live on the
          linked Profile record and can be updated here.
        </p>

        {error ? (
          <div className="mt-4">
            <ErrorPanel title="Profile could not be saved" message={error} />
          </div>
        ) : null}
        {saved ? (
          <div role="status" className="mt-4 border border-accent bg-accent-soft px-4 py-3 text-sm text-sidebar">
            Profile contact details saved.
          </div>
        ) : null}

        <form className="mt-6 flex flex-col gap-4" onSubmit={onSubmit}>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-foreground">Email (User)</span>
            <input
              value={me?.email ?? ""}
              readOnly
              className="border border-border bg-background px-3 py-2 text-muted"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-foreground">Name (Profile)</span>
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="border border-border px-3 py-2"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-foreground">Phone (Profile)</span>
            <input
              value={phone}
              onChange={(event) => setPhone(event.target.value)}
              className="border border-border px-3 py-2"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-foreground">Address (Profile)</span>
            <input
              value={address}
              onChange={(event) => setAddress(event.target.value)}
              className="border border-border px-3 py-2"
            />
          </label>
          <div className="mt-2 flex flex-wrap gap-3">
            <button
              type="submit"
              disabled={saving}
              className="bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-sidebar-hover disabled:opacity-60"
            >
              {saving ? "Saving…" : "Save profile"}
            </button>
            <a
              href="/account/change-password"
              className="border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-background"
            >
              Change password
            </a>
            <button
              type="button"
              onClick={() => logoutAndRedirect()}
              className="border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-background"
            >
              Log out
            </button>
          </div>
        </form>
        {profile ? (
          <p className="mt-4 text-xs text-muted">Profile id {profile?.id ?? ""}</p>
        ) : null}
      </section>
    </div>
  );
}
