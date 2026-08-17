"use client";

import { useCallback, useRef, useState } from "react";
import { ErrorPanel } from "@/components/ErrorPanel";
import {
  analyzeIncidentFile,
  exportResultsUrl,
  type IncidentAnalysis,
} from "@/lib/incidentApi";
import { toUserFacingMessage, USER_MESSAGES, messageForStatus } from "@/lib/userFacingError";

function pct(part: number, whole: number): string {
  if (whole <= 0) return "0.0%";
  return `${((part / whole) * 100).toFixed(1)}%`;
}

function MetricList({
  title,
  rows,
}: {
  title: string;
  rows: Array<{ label: string; value: string }>;
}) {
  return (
    <section className="border border-border bg-surface px-4 py-5">
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      <ul className="mt-4 divide-y divide-panel-line">
        {rows.map((row) => (
          <li
            key={row.label}
            className="flex items-center justify-between gap-4 py-2 text-sm"
          >
            <span className="text-muted">{row.label}</span>
            <span className="font-medium text-foreground">{row.value}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

type AnalysisUi = "idle" | "loading" | "fulfilled" | "rejected";

export function IncidentAnalysisPanel() {
  const inputRef = useRef<HTMLInputElement>(null);
  const lastFileRef = useRef<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<IncidentAnalysis | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [uiState, setUiState] = useState<AnalysisUi>("idle");
  const [exportError, setExportError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  const runAnalysis = useCallback((file: File) => {
    lastFileRef.current = file;
    setError(null);
    setExportError(null);
    setFileName(file.name);
    setUiState("loading");
    void (async () => {
      try {
        const analysis = await analyzeIncidentFile(file);
        setResult(analysis);
        setUiState("fulfilled");
      } catch (err) {
        setResult(null);
        setError(toUserFacingMessage(err));
        setUiState("rejected");
      } finally {
        setUiState((current) => (current === "loading" ? "rejected" : current));
      }
    })();
  }, []);

  const onFiles = useCallback(
    (files: FileList | null) => {
      const file = files?.[0];
      if (!file) return;
      runAnalysis(file);
    },
    [runAnalysis]
  );

  async function downloadExport() {
    setExportError(null);
    setExporting(true);
    try {
      let response: Response;
      try {
        response = await fetch(exportResultsUrl());
      } catch {
        setExportError(USER_MESSAGES.connection);
        return;
      }
      if (!response.ok) {
        setExportError(messageForStatus(response.status));
        return;
      }
      try {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = "results.csv";
        anchor.click();
        URL.revokeObjectURL(url);
      } catch {
        setExportError(USER_MESSAGES.parse);
      }
    } finally {
      setExporting(false);
    }
  }

  const isPending = uiState === "loading";
  const invalidBreakdown = result?.invalid_breakdown ?? {};
  const invalidRows =
    result == null
      ? []
      : Object.entries(invalidBreakdown)
          .filter(([, count]) => count > 0)
          .map(([rule, count]) => ({
            label: result.invalid_breakdown_labels?.[rule] ?? rule,
            value: String(count),
          }));

  const satisfaction = result?.satisfaction;
  const scoredCases = satisfaction?.scored_cases ?? 0;
  const closedCases = satisfaction?.closed_cases ?? 0;
  const satisfactionCounts = satisfaction?.counts ?? {};

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
      </section>

      <section
        className={`border border-dashed px-6 py-10 transition-colors ${
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
          {fileName ? (
            <p className="mt-3 text-xs text-muted">Selected: {fileName}</p>
          ) : null}
        </div>
      </section>

      {isPending ? (
        <div className="loading-state border border-border bg-surface px-4 py-8 text-center text-sm text-muted">
          Analyzing incident file…
        </div>
      ) : null}

      {uiState === "rejected" && error ? (
        <ErrorPanel
          title="Upload could not be analyzed"
          message={error}
          onRetry={() => {
            const file = lastFileRef.current;
            if (file) runAnalysis(file);
          }}
        />
      ) : null}

      {result && (result.invalid_records ?? 0) > 0 ? (
        <div
          role="status"
          className="border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950"
        >
          <p className="font-semibold">
            {result.invalid_records} invalid / incomplete record
            {result.invalid_records === 1 ? "" : "s"} excluded from analytics
          </p>
          <ul className="mt-2 list-disc pl-5">
            {invalidRows.map((row) => (
              <li key={row.label}>
                {row.label}: {row.value}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {uiState === "fulfilled" && result ? (
        <>
          <section className="grid gap-4 md:grid-cols-3">
            <div className="border border-border bg-surface px-4 py-5">
              <p className="text-xs uppercase tracking-[0.14em] text-muted">
                Total records
              </p>
              <p className="mt-2 font-display text-3xl text-foreground">
                {result.total_records ?? 0}
              </p>
            </div>
            <div className="border border-border bg-surface px-4 py-5">
              <p className="text-xs uppercase tracking-[0.14em] text-muted">
                Valid
              </p>
              <p className="mt-2 font-display text-3xl text-foreground">
                {result.valid_records ?? 0}
              </p>
            </div>
            <div className="border border-border bg-surface px-4 py-5">
              <p className="text-xs uppercase tracking-[0.14em] text-muted">
                Invalid
              </p>
              <p className="mt-2 font-display text-3xl text-foreground">
                {result.invalid_records ?? 0}
              </p>
            </div>
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <MetricList
              title="Category breakdown"
              rows={Object.entries(result.by_category ?? {}).map(([label, count]) => ({
                label,
                value: `${count} (${pct(count, result.valid_records ?? 0)})`,
              }))}
            />
            <MetricList
              title="Status lifecycle"
              rows={Object.entries(result.by_status ?? {}).map(([label, count]) => ({
                label,
                value: `${count} (${pct(count, result.valid_records ?? 0)})`,
              }))}
            />
            <MetricList
              title="Country breakdown"
              rows={Object.entries(result.by_country ?? {}).map(([label, count]) => ({
                label,
                value: `${count} (${pct(count, result.valid_records ?? 0)})`,
              }))}
            />
            <MetricList
              title="Satisfaction index (closed)"
              rows={[
                {
                  label: "Scored cases",
                  value: `${scoredCases} of ${closedCases}`,
                },
                {
                  label: "Average score",
                  value:
                    satisfaction?.average == null
                      ? "n/a"
                      : `${satisfaction.average.toFixed(2)} / 5.00`,
                },
                ...[1, 2, 3, 4, 5].map((score) => ({
                  label: `Score ${score}`,
                  value: String(satisfactionCounts[String(score)] ?? 0),
                })),
              ]}
            />
          </section>

          {exportError ? (
            <ErrorPanel
              title="Results could not be downloaded"
              message={exportError}
              onRetry={() => void downloadExport()}
            />
          ) : null}

          <div>
            <button
              type="button"
              onClick={() => void downloadExport()}
              disabled={exporting}
              className="inline-flex bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sidebar-hover disabled:opacity-60"
            >
              {exporting ? "Preparing download…" : "Download results.csv"}
            </button>
          </div>
        </>
      ) : null}
    </div>
  );
}
