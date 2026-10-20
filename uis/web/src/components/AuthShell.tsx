"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { forwardedPortUrl } from "@/lib/forwardedPort";

export function AuthShell({
  title,
  subtitle,
  showWebsiteLink = false,
  children,
}: {
  title: string;
  subtitle: string;
  showWebsiteLink?: boolean;
  children: React.ReactNode;
}) {
  const [websiteUrl, setWebsiteUrl] = useState<string | null>(null);

  useEffect(() => {
    if (showWebsiteLink) setWebsiteUrl(forwardedPortUrl(3000));
  }, [showWebsiteLink]);

  return (
    <div className="flex min-h-full flex-1 items-center justify-center bg-background px-4 py-12">
      <div className="w-full max-w-md">
        {websiteUrl ? (
          <a
            href={websiteUrl}
            className="mb-6 block text-center text-sm text-accent underline-offset-2 hover:underline"
          >
            ← Back to HealthCore website
          </a>
        ) : null}
        <p className="text-center font-display text-2xl text-sidebar">HealthCore</p>
        <p className="mt-1 text-center text-xs uppercase tracking-[0.16em] text-muted">
          Internal staff access
        </p>
        <section className="mt-8 border border-border bg-surface px-6 py-8">
          <h1 className="font-display text-2xl text-foreground">{title}</h1>
          <p className="mt-2 text-sm leading-6 text-muted">{subtitle}</p>
          <div className="mt-6">{children}</div>
        </section>
        <p className="mt-4 text-center text-xs text-muted">
          Public patient site is separate and does not use this login.{" "}
          <Link href="/login" className="text-accent underline-offset-2 hover:underline">
            Sign in
          </Link>
          {" · "}
          <Link href="/register" className="text-accent underline-offset-2 hover:underline">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}
