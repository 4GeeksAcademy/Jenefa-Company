"use client";

import Link from "next/link";
import { SUPPORT_EMAIL, SUPPORT_PHONE } from "@/lib/userFacingError";

export function ErrorPanel({
  title = "Something went wrong",
  message,
  onRetry,
  retryLabel = "Retry",
}: {
  title?: string;
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
}) {
  return (
    <div
      role="alert"
      className="border border-red-300 bg-red-50 px-4 py-4 text-sm text-red-900"
    >
      <p className="font-semibold">{title}</p>
      <p className="mt-1">{message}</p>
      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2">
        {onRetry ? (
          <button
            type="button"
            onClick={onRetry}
            className="bg-accent px-3 py-1.5 text-sm font-medium text-white hover:bg-sidebar-hover"
          >
            {retryLabel}
          </button>
        ) : null}
        <Link
          href="/"
          className="font-medium text-accent underline-offset-2 hover:underline"
        >
          Return home
        </Link>
        <a
          href={`mailto:${SUPPORT_EMAIL}`}
          className="font-medium text-accent underline-offset-2 hover:underline"
        >
          Contact support ({SUPPORT_EMAIL})
        </a>
      </div>
      <p className="mt-2 text-xs text-red-800/80">
        HealthCore Digital support: {SUPPORT_PHONE}
      </p>
    </div>
  );
}
