import type { ReactNode } from "react";
import Link from "next/link";
import type { UIState } from "@/types";
import { SUPPORT_EMAIL, SUPPORT_PHONE } from "@/lib/userFacingError";

interface AsyncStateViewProps {
  uiState: UIState;
  error: string | null;
  loadingMessage?: string;
  onRetry?: () => void;
  children: ReactNode;
}

export function AsyncStateView({
  uiState,
  error,
  loadingMessage = "Loading data from HealthCore systems…",
  onRetry,
  children,
}: AsyncStateViewProps) {
  if (uiState === "loading") {
    return (
      <div className="rounded-lg border border-teal-200 bg-teal-50 px-6 py-8 text-center text-teal-800">
        <p className="font-medium">{loadingMessage}</p>
      </div>
    );
  }

  if (uiState === "error") {
    return (
      <div
        role="alert"
        className="rounded-lg border border-red-200 bg-red-50 px-6 py-8 text-center text-red-800"
      >
        <p className="font-medium">Unable to load data</p>
        <p className="mt-2 text-sm">
          {error ??
            "We're experiencing temporary connection issues. Your data hasn't been lost. (Error 0)"}
        </p>
        <div className="mt-4 flex flex-wrap items-center justify-center gap-3">
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="rounded-md bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-800"
            >
              Try again
            </button>
          )}
          <Link
            href="/"
            className="text-sm font-medium text-teal-800 underline-offset-2 hover:underline"
          >
            Return home
          </Link>
          <a
            href={`mailto:${SUPPORT_EMAIL}`}
            className="text-sm font-medium text-teal-800 underline-offset-2 hover:underline"
          >
            Contact support
          </a>
        </div>
        <p className="mt-3 text-xs text-red-700">
          HealthCore Digital support: {SUPPORT_PHONE} · {SUPPORT_EMAIL}
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
