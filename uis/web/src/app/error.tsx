"use client";

import { ErrorPanel } from "@/components/ErrorPanel";
import { messageForStatus } from "@/lib/userFacingError";

export default function AppError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="mx-auto w-full max-w-2xl px-4 py-16">
      <ErrorPanel
        title="This page could not be displayed"
        message={messageForStatus(500)}
        onRetry={reset}
      />
    </div>
  );
}
