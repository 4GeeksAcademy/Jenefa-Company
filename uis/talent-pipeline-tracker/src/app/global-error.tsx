"use client";

import { SUPPORT_EMAIL, SUPPORT_PHONE, USER_MESSAGES } from "@/lib/userFacingError";

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body className="min-h-full bg-slate-50 px-4 py-16 font-sans text-slate-900">
        <div
          role="alert"
          className="mx-auto max-w-xl rounded-lg border border-red-200 bg-red-50 px-6 py-8 text-center text-red-800"
        >
          <p className="font-medium">HealthCore could not load this workspace</p>
          <p className="mt-2 text-sm">{USER_MESSAGES.generic}</p>
          <div className="mt-4 flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              onClick={reset}
              className="rounded-md bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-800"
            >
              Try again
            </button>
            <a href="/" className="text-sm font-medium text-teal-800 underline">
              Return home
            </a>
            <a
              href={`mailto:${SUPPORT_EMAIL}`}
              className="text-sm font-medium text-teal-800 underline"
            >
              Contact support
            </a>
          </div>
          <p className="mt-3 text-xs text-red-700">
            {SUPPORT_PHONE} · {SUPPORT_EMAIL}
          </p>
        </div>
      </body>
    </html>
  );
}
