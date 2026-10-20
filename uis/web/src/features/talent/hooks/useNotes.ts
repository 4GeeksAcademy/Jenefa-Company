"use client";

import { useCallback } from "react";
import { createNote, deleteNote, fetchNotes } from "@/features/talent/services/notes";
import { useAsyncState, useMountEffect } from "@/features/talent/hooks/useAsyncState";
import type { Note } from "@/features/talent/types";

export function useNotes(recordId: string) {
  const { data, uiState, error, setData, run } = useAsyncState<Note[]>([]);

  const load = useCallback(async () => {
    return run(() => fetchNotes(recordId));
  }, [recordId, run]);

  useMountEffect(() => {
    void load();
  });

  const addNote = useCallback(
    async (content: string) => {
      try {
        await createNote(recordId, { content });
        const refreshed = await fetchNotes(recordId);
        setData(refreshed);
        return { success: true as const };
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to add evaluation note";
        return { success: false as const, error: message };
      }
    },
    [recordId, setData],
  );

  const removeNote = useCallback(
    async (noteId: string) => {
      try {
        await deleteNote(recordId, noteId);
        setData((prev) => (prev ?? []).filter((note) => note.id !== noteId));
        return { success: true as const };
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to delete evaluation note";
        return { success: false as const, error: message };
      }
    },
    [recordId, setData],
  );

  return {
    notes: data ?? [],
    uiState,
    error,
    reload: load,
    addNote,
    removeNote,
  };
}
