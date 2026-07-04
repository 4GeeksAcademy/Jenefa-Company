"use client";

import { useCallback } from "react";
import { fetchRecordById } from "@/services/records";
import { useAsyncState, useMountEffect } from "@/hooks/useAsyncState";
import type { Candidate } from "@/types";

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
