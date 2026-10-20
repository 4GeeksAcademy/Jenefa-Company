"use client";

import { useEffect, useRef, useState } from "react";

import { apiFetch, readJson } from "@/lib/api";

const POLL_INTERVAL_MS = 2000;
const MAX_POLLS = 60;

type RefreshState = { phase: "idle" | "running" | "done" | "error"; message: string };

export function ReportingRefresh({ onCompleted }: { onCompleted?: () => void | Promise<void> }) {
  const [state, setState] = useState<RefreshState>({ phase: "idle", message: "" });
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => () => {
    if (timer.current) clearTimeout(timer.current);
  }, []);

  async function pollRun(taskId: string, attempt: number) {
    try {
      const response = await apiFetch(`/services/reporting/trigger/${taskId}`);
      const body = await readJson<{ status: string }>(response);
      if (body.status === "success") {
        setState({ phase: "done", message: "Reporting run completed." });
        await onCompleted?.();
        return;
      }
      if (body.status === "failure") {
        setState({ phase: "error", message: "Reporting run failed. Check the worker logs." });
        return;
      }
      if (attempt >= MAX_POLLS) {
        setState({ phase: "error", message: "Run is still in progress. Refresh this page later." });
        return;
      }
      setState({ phase: "running", message: `Run ${body.status}…` });
      timer.current = setTimeout(() => void pollRun(taskId, attempt + 1), POLL_INTERVAL_MS);
    } catch (cause) {
      setState({
        phase: "error",
        message: cause instanceof Error ? cause.message : "Unable to check run status.",
      });
    }
  }

  async function startRun() {
    setState({ phase: "running", message: "Queuing run…" });
    try {
      const response = await apiFetch("/services/reporting/trigger", { method: "POST" });
      const body = await readJson<{ task_id: string }>(response);
      void pollRun(body.task_id, 1);
    } catch (cause) {
      setState({
        phase: "error",
        message: cause instanceof Error ? cause.message : "Unable to start the reporting run.",
      });
    }
  }

  return (
    <div className="flex flex-col items-start gap-2 sm:items-end">
      <button
        type="button"
        onClick={() => void startRun()}
        disabled={state.phase === "running"}
        className="border border-border bg-surface px-4 py-2 text-sm font-medium text-foreground hover:bg-panel-line/40 disabled:opacity-60"
      >
        {state.phase === "running" ? "Running…" : "Refresh reporting data"}
      </button>
      {state.message ? (
        <p role="status" className={state.phase === "error" ? "text-sm text-red-900" : "text-sm text-muted"}>
          {state.message}
        </p>
      ) : null}
    </div>
  );
}
