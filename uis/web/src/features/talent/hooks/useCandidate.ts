"use client";

import { useCallback } from "react";
import { fetchRecordById } from "@/features/talent/services/records";
import { useAsyncState, useMountEffect } from "@/features/talent/hooks/useAsyncState";
import type { Candidate } from "@/features/talent/types";

export function useCandidate(id: string) {
  const { data, uiState, error, setData, run } = useAsyncState<Candidate | null>(
    null,
  );

  const load = useCallback(async () => {
    return run(() => fetchRecordById(id));
  }, [id, run]);

  useMountEffect(() => {
    void load();
  });

  return { candidate: data, uiState, error, reload: load, setCandidate: setData };
}
