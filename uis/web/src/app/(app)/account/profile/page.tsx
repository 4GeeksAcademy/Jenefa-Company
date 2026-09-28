"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  fetchMe,
  fetchMyProfile,
  updateMyProfile,
  type MeResponse,
  type Profile,
} from "@/lib/authApi";
import { ApiRequestError } from "@/lib/api";
import { logoutAndRedirect } from "@/lib/authStorage";

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

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [mePayload, profilePayload] = await Promise.all([fetchMe(), fetchMyProfile()]);
        if (cancelled) return;
        setMe(mePayload);
        setProfile(profilePayload);
        setName(profilePayload.name);
        setPhone(profilePayload.phone);
        setAddress(profilePayload.address);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Unable to load profile.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
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
      const message =
        err instanceof ApiRequestError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Unable to update profile.";
      setError(message);
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
          <div role="alert" className="mt-4 border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900">
            {error}
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
          <p className="mt-4 text-xs text-muted">Profile id {profile.id}</p>
        ) : null}
      </section>
    </div>
  );
}
