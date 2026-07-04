"use client";

import { useCallback, useEffect, useState, type Dispatch, type SetStateAction } from "react";
import type { UIState } from "@/types";

interface AsyncState<T> {
  data: T | null;
  uiState: UIState;
  error: string | null;
  setData: Dispatch<SetStateAction<T | null>>;
  setUiState: (state: UIState) => void;
  setError: (error: string | null) => void;
  run: (operation: () => Promise<T>) => Promise<T | null>;
}

export function useAsyncState<T>(initialData: T | null = null): AsyncState<T> {
  const [data, setData] = useState<T | null>(initialData);
  const [uiState, setUiState] = useState<UIState>(
    initialData ? "success" : "loading",
  );
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async (operation: () => Promise<T>) => {
    setUiState("loading");
    setError(null);
    try {
      const result = await operation();
      setData(result);
      setUiState("success");
      return result;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "An unexpected error occurred";
      setError(message);
      setUiState("error");
      return null;
    }
  }, []);

  return { data, uiState, error, setData, setUiState, setError, run };
}

export function useMountEffect(effect: () => void | (() => void)) {
  useEffect(() => {
    return effect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}
