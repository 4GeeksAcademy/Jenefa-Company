"use client";

import { CandidateForm } from "@/features/talent/components/CandidateForm";
import { AsyncStateView } from "@/features/talent/components/AsyncStateView";
import { useCandidate } from "@/features/talent/hooks/useCandidate";

export function EditCandidatePage({ id }: { id: string }) {
  const { candidate, uiState, error, reload } = useCandidate(id);

  return (
    <AsyncStateView
      uiState={uiState}
      error={error}
      loadingMessage="Loading applicant record for editing…"
      onRetry={() => void reload()}
    >
      {candidate && <CandidateForm mode="edit" candidate={candidate} />}
    </AsyncStateView>
  );
}
