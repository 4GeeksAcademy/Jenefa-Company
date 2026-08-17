"use client";

import { useState } from "react";
import { AsyncStateView } from "@/components/AsyncStateView";
import { useNotes } from "@/hooks/useNotes";

export function NotesSection({ recordId }: { recordId: string }) {
  const { notes, uiState, error, reload, addNote, removeNote } = useNotes(recordId);
  const [text, setText] = useState("");
  const [submitState, setSubmitState] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [submitMessage, setSubmitMessage] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) {
      setSubmitState("error");
      setSubmitMessage("Evaluation note cannot be empty.");
      return;
    }

    setSubmitState("loading");
    setSubmitMessage(null);
    try {
      const result = await addNote(trimmed);
      if (result.success) {
        setText("");
        setSubmitState("success");
        setSubmitMessage("Evaluation note added to applicant timeline.");
      } else {
        setSubmitState("error");
        setSubmitMessage(result.error);
      }
    } finally {
      setSubmitState((current) => (current === "loading" ? "error" : current));
    }
  };

  const handleDelete = async (noteId: string) => {
    setDeletingId(noteId);
    try {
      const result = await removeNote(noteId);
      if (!result.success) {
        setSubmitState("error");
        setSubmitMessage(result.error);
      }
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-900">
        Timeline Evaluation Stream
      </h3>
      <p className="mt-1 text-sm text-slate-600">
        Internal interview notes for the People & Workforce team. Not visible to applicants.
      </p>

      <form onSubmit={(event) => void handleSubmit(event)} className="mt-4 space-y-3">
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">
            Add evaluation note
          </span>
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            rows={3}
            placeholder="Document interview feedback, credential checks, or hiring committee notes…"
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600"
          />
        </label>
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="submit"
            disabled={submitState === "loading"}
            className="rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800 disabled:opacity-60"
          >
            {submitState === "loading" ? "Saving…" : "Add note"}
          </button>
          {submitState === "success" && submitMessage && (
            <p className="text-sm text-emerald-700">{submitMessage}</p>
          )}
          {submitState === "error" && submitMessage && (
            <p className="text-sm text-red-700">{submitMessage}</p>
          )}
        </div>
      </form>

      <div className="mt-6">
        <AsyncStateView
          uiState={uiState}
          error={error}
          loadingMessage="Loading evaluation notes…"
          onRetry={() => void reload()}
        >
          {notes.length === 0 ? (
            <p className="text-sm text-slate-500">No evaluation notes yet.</p>
          ) : (
            <ul className="space-y-3">
              {notes.map((note) => (
                <li
                  key={note.id}
                  className="rounded-md border border-slate-200 bg-slate-50 px-4 py-3"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm text-slate-800">{note.content}</p>
                      <p className="mt-2 text-xs text-slate-500">
                        {new Date(note.created_at).toLocaleString("en-GB")}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => void handleDelete(note.id)}
                      disabled={deletingId === note.id}
                      className="shrink-0 text-xs font-medium text-red-700 hover:text-red-900 disabled:opacity-60"
                    >
                      {deletingId === note.id ? "Removing…" : "Delete"}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </AsyncStateView>
      </div>
    </section>
  );
}
