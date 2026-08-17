"use client";

import { messageForStatus } from "@/lib/userFacingError";
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
      error={messageForStatus(500)}
      onRetry={reset}
    >
      {null}
    </AsyncStateView>
  );
}
