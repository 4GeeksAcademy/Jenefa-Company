"use client";

import { useCallback, useState } from "react";
import { getIncidentSummary, type IncidentSummary } from "@/lib/incidentApi";
import {
  BRANCH_LABELS,
  CATEGORY_LABELS,
  ORIGIN_LABELS,
  STATUS_LABELS,
} from "@/lib/incidentLabels";

function MetricGrid({
  title,
  rows,
}: {
  title: string;
  rows: Array<{ label: string; value: number }>;
}) {
  return (
    <section className="border border-border bg-white px-4 py-4">
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      <ul className="mt-3 divide-y divide-panel-line">
        {rows.map((row) => (
          <li
            key={row.label}
            className="flex items-center justify-between gap-3 py-2 text-sm"
          >
            <span className="text-muted">{row.label}</span>
            <span className="font-medium text-foreground">{row.value}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function IncidentSummaryPanel({
  initialSummary,
  initialError = null,
}: {
  initialSummary: IncidentSummary | null;
  initialError?: string | null;
}) {
  const [summary, setSummary] = useState<IncidentSummary | null>(initialSummary);
  const [error, setError] = useState<string | null>(initialError);
  const [isLoading, setIsLoading] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const payload = await getIncidentSummary();
      setSummary(payload);
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Summary could not be loaded.";
      setError(message);
      setSummary(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return (
    <section className="border border-border bg-surface px-6 py-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="font-display text-2xl text-foreground">Summary panel</h2>
          <p className="mt-2 text-sm text-muted">
            Aggregated totals by status, category, origin, and branch.
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            setSummary(null);
            setError(null);
            void load();
          }}
          className="border border-border bg-white px-3 py-2 text-sm text-foreground hover:bg-background"
        >
          Refresh
        </button>
      </div>

      {isLoading ? <p className="mt-5 text-sm text-muted">Loading summary...</p> : null}

      {error ? (
        <div className="mt-5 border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900">
          <p className="font-semibold">Summary request failed.</p>
          <p className="mt-1">{error}</p>
        </div>
      ) : null}

      {!isLoading && !error && summary ? (
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <MetricGrid
            title="By status"
            rows={Object.entries(summary.status).map(([key, value]) => ({
              label: STATUS_LABELS[key as keyof typeof STATUS_LABELS],
              value,
            }))}
          />
          <MetricGrid
            title="By category"
            rows={Object.entries(summary.category).map(([key, value]) => ({
              label: CATEGORY_LABELS[key as keyof typeof CATEGORY_LABELS],
              value,
            }))}
          />
          <MetricGrid
            title="By origin"
            rows={Object.entries(summary.origin).map(([key, value]) => ({
              label: ORIGIN_LABELS[key as keyof typeof ORIGIN_LABELS],
              value,
            }))}
          />
          <MetricGrid
            title="By branch"
            rows={Object.entries(summary.branch).map(([key, value]) => ({
              label: BRANCH_LABELS[key as keyof typeof BRANCH_LABELS],
              value,
            }))}
          />
        </div>
      ) : null}
    </section>
  );
}
