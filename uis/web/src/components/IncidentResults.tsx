import {
  exportResultsUrl,
  type IncidentAnalysis,
} from "@/lib/incidentApi";

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

export function IncidentResults({ result }: { result: IncidentAnalysis }) {
  const invalidRows = Object.entries(result.invalid_breakdown)
    .filter(([, count]) => count > 0)
    .map(([rule, count]) => ({
      label: result.invalid_breakdown_labels?.[rule] ?? rule,
      value: String(count),
    }));

  return (
    <>
      {result.invalid_records > 0 ? (
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

      <section className="grid gap-4 md:grid-cols-3">
        <div className="border border-border bg-surface px-4 py-5">
          <p className="text-xs uppercase tracking-[0.14em] text-muted">
            Total records
          </p>
          <p className="mt-2 font-display text-3xl text-foreground">
            {result.total_records}
          </p>
        </div>
        <div className="border border-border bg-surface px-4 py-5">
          <p className="text-xs uppercase tracking-[0.14em] text-muted">
            Valid
          </p>
          <p className="mt-2 font-display text-3xl text-foreground">
            {result.valid_records}
          </p>
        </div>
        <div className="border border-border bg-surface px-4 py-5">
          <p className="text-xs uppercase tracking-[0.14em] text-muted">
            Invalid
          </p>
          <p className="mt-2 font-display text-3xl text-foreground">
            {result.invalid_records}
          </p>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <MetricList
          title="Category breakdown"
          rows={Object.entries(result.by_category).map(([label, count]) => ({
            label,
            value: `${count} (${pct(count, result.valid_records)})`,
          }))}
        />
        <MetricList
          title="Status lifecycle"
          rows={Object.entries(result.by_status).map(([label, count]) => ({
            label,
            value: `${count} (${pct(count, result.valid_records)})`,
          }))}
        />
        <MetricList
          title="Country breakdown"
          rows={Object.entries(result.by_country).map(([label, count]) => ({
            label,
            value: `${count} (${pct(count, result.valid_records)})`,
          }))}
        />
        <MetricList
          title="Satisfaction index (closed)"
          rows={[
            {
              label: "Scored cases",
              value: `${result.satisfaction.scored_cases} of ${result.satisfaction.closed_cases}`,
            },
            {
              label: "Average score",
              value:
                result.satisfaction.average == null
                  ? "n/a"
                  : `${result.satisfaction.average.toFixed(2)} / 5.00`,
            },
            ...[1, 2, 3, 4, 5].map((score) => ({
              label: `Score ${score}`,
              value: String(result.satisfaction.counts[String(score)] ?? 0),
            })),
          ]}
        />
      </section>

      <div>
        <a
          href={exportResultsUrl()}
          className="inline-flex bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sidebar-hover"
        >
          Download results.csv
        </a>
      </div>
    </>
  );
}
