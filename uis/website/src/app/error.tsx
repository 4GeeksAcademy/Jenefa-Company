"use client";

import Link from "next/link";
import { siteConfig } from "@/lib/site";

export default function AppError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="mx-auto w-full max-w-xl px-4 py-16">
      <div
        role="alert"
        className="rounded-2xl border border-rose-600 bg-rose-500/10 p-6 text-rose-800"
      >
        <p className="font-semibold">This page could not be displayed</p>
        <p className="mt-2 text-sm">
          We couldn&apos;t complete that request. Please try again. (Error 500)
        </p>
        <div className="mt-4 flex flex-wrap gap-4 text-sm font-medium">
          <button
            type="button"
            onClick={reset}
            className="rounded-full bg-accent-500 px-4 py-2 text-white hover:bg-accent-600"
          >
            Retry
          </button>
          <Link href="/" className="underline-offset-2 hover:underline">
            Return home
          </Link>
          <a href={`mailto:${siteConfig.email}`} className="underline-offset-2 hover:underline">
            Contact support
          </a>
        </div>
        <p className="mt-3 text-xs">
          {siteConfig.phone} · {siteConfig.email}
        </p>
      </div>
    </div>
  );
}
