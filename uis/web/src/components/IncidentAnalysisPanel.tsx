"use client";

import { useCallback, useEffect, useRef, useState, useTransition } from "react";
import {
  analyzeIncidentFile,
  fetchLatestIncidentAnalysis,
  type IncidentAnalysis,
} from "@/lib/incidentApi";
import { IncidentResults } from "@/components/IncidentResults";

export function IncidentAnalysisPanel() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [result, setResult] = useState<IncidentAnalysis | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    let active = true;
    fetchLatestIncidentAnalysis()
      .then((latest) => {
        if (active && latest) setResult(latest);
      })
      .catch((err: unknown) => {
        if (active) setLoadError(err instanceof Error ? err.message : "Latest analysis could not be loaded.");
      });
    return () => {
      active = false;
    };
  }, []);

  const runAnalysis = useCallback((file: File) => {
    setError(null);
    startTransition(async () => {
      try {
        const analysis = await analyzeIncidentFile(file);
        setResult(analysis);
        setLoadError(null);
      } catch (err) {
        // The server keeps the previous analysis on a failed upload, so keep showing it here too.
        setError(err instanceof Error ? err.message : "Analysis failed.");
      }
    });
  }, []);

  const onFiles = useCallback(
    (files: FileList | null) => {
      const file = files?.[0];
      if (!file) return;
      runAnalysis(file);
    },
    [runAnalysis]
  );

  return (
    <div className="flex flex-col gap-8">
      <section className="rounded-lg border border-border bg-surface px-6 py-8">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">
          Patient experience
        </p>
        <h2 className="mt-2 font-display text-3xl tracking-tight text-foreground">
          Incident analysis
        </h2>
        <p className="mt-3 max-w-2xl text-base leading-7 text-muted">
          Upload a clinic incident CSV for aggregate validation. Outputs never
          include patient identifiers — HIPAA / UK GDPR safe summaries only.
        </p>

        <div
          className={`mt-8 border border-dashed px-6 py-10 transition-colors ${
            dragOver
              ? "border-accent bg-accent-soft"
              : "border-border bg-surface"
          }`}
          onDragEnter={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={(e) => {
            e.preventDefault();
            setDragOver(false);
          }}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            onFiles(e.dataTransfer.files);
          }}
        >
          <div className="mx-auto flex max-w-lg flex-col items-center text-center">
            <p className="font-display text-xl text-foreground">
              Drop incident CSV here
            </p>
            <p className="mt-2 text-sm text-muted">
              UTF-8 comma-separated file with HealthCore incident headers
            </p>
            <button
              type="button"
              className="mt-5 bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sidebar-hover"
              onClick={() => inputRef.current?.click()}
              disabled={isPending}
            >
              {isPending ? "Analyzing…" : "Choose file"}
            </button>
            <input
              ref={inputRef}
              type="file"
              accept=".csv,text/csv"
              className="sr-only"
              onChange={(e) => onFiles(e.target.files)}
            />
          </div>
        </div>
      </section>

      {loadError ? (
        <p role="alert" className="text-sm text-red-900">
          Latest analysis could not be loaded: {loadError}
        </p>
      ) : null}

      {error ? (
        <div
          role="alert"
          className="border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900"
        >
          <p className="font-semibold">Upload could not be analyzed</p>
          <p className="mt-1">{error}</p>
        </div>
      ) : null}

      {result ? <IncidentResults result={result} /> : null}
    </div>
  );
}
