"use client";

import { ErrorPanel } from "@/components/ErrorPanel";
import { USER_MESSAGES } from "@/lib/userFacingError";

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body className="min-h-full bg-[#f4f7f8] px-4 py-16 font-sans text-[#1a2b32]">
        <div className="mx-auto w-full max-w-2xl">
          <ErrorPanel
            title="HealthCore could not load this workspace"
            message={USER_MESSAGES.generic}
            onRetry={reset}
          />
        </div>
      </body>
    </html>
  );
}
