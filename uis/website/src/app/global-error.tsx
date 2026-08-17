"use client";

import { siteConfig } from "@/lib/site";

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body className="min-h-full bg-white px-4 py-16 font-sans text-slate-900">
        <div
          role="alert"
          className="mx-auto max-w-xl rounded-2xl border border-rose-600 bg-rose-500/10 p-6 text-rose-800"
        >
          <p className="font-semibold">HealthCore could not load this page</p>
          <p className="mt-2 text-sm">
            We couldn&apos;t complete that request. Please try again. (Error 500)
          </p>
          <div className="mt-4 flex flex-wrap gap-4 text-sm font-medium">
            <button type="button" onClick={reset}>
              Retry
            </button>
            <a href="/">Return home</a>
            <a href={`mailto:${siteConfig.email}`}>Contact support</a>
          </div>
          <p className="mt-3 text-xs">
            {siteConfig.phone} · {siteConfig.email}
          </p>
        </div>
      </body>
    </html>
  );
}
