import type { ReactNode } from "react";
import type { UIState } from "@/types";

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
      <div className="rounded-lg border border-red-200 bg-red-50 px-6 py-8 text-center text-red-800">
        <p className="font-medium">Unable to load data</p>
        <p className="mt-2 text-sm">{error ?? "An unexpected error occurred."}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-4 rounded-md bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-800"
          >
            Try again
          </button>
        )}
      </div>
    );
  }

  return <>{children}</>;
}
