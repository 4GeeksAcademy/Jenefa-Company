import { apiRequest } from "@/services/api";
import type { Note, NoteCreatePayload, NotesListResponse } from "@/types";

export async function fetchNotes(recordId: string): Promise<Note[]> {
  const response = await apiRequest<NotesListResponse>(
    `/records/${recordId}/notes`,
  );
  return response.data;
}

export async function createNote(
  recordId: string,
  payload: NoteCreatePayload,
): Promise<void> {
  await apiRequest<void>(`/records/${recordId}/notes`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteNote(
  recordId: string,
  noteId: string,
): Promise<void> {
  await apiRequest<void>(`/records/${recordId}/notes/${noteId}`, {
    method: "DELETE",
  });
}
