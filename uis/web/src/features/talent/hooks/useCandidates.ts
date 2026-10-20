"use client";

import { useCallback } from "react";
import { fetchRecords } from "@/features/talent/services/records";
import { useAsyncState, useMountEffect } from "@/features/talent/hooks/useAsyncState";
import type { Candidate } from "@/features/talent/types";

export function useCandidates() {
  const { data, uiState, error, setData, run } = useAsyncState<Candidate[]>([]);

  const load = useCallback(async () => {
    return run(() => fetchRecords());
  }, [run]);

  useMountEffect(() => {
    void load();
  });

  return { candidates: data ?? [], uiState, error, reload: load, setCandidates: setData };
}
