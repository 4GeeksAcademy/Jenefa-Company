"use client";

import { CandidateForm } from "@/components/CandidateForm";
import { AsyncStateView } from "@/components/AsyncStateView";
import { useCandidate } from "@/hooks/useCandidate";

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
