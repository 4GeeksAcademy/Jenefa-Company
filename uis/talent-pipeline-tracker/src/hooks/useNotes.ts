"use client";

import { useCallback } from "react";
import { createNote, deleteNote, fetchNotes } from "@/services/notes";
import { useAsyncState, useMountEffect } from "@/hooks/useAsyncState";
import { toUserFacingMessage } from "@/lib/userFacingError";
import type { Note } from "@/types";

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
        return { success: false as const, error: toUserFacingMessage(err) };
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
        return { success: false as const, error: toUserFacingMessage(err) };
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
