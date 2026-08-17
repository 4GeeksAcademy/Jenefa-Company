"use client";

import { USER_MESSAGES } from "@/lib/userFacingError";
import { AsyncStateView } from "@/components/AsyncStateView";

export default function AppError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <AsyncStateView
      uiState="error"
      error={USER_MESSAGES.generic}
      onRetry={reset}
    >
      {null}
    </AsyncStateView>
  );
}
