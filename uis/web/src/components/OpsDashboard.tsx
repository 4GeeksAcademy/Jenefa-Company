import { buildOpsDashboardSnapshot } from "healthcore-testing";

function formatPercent(value: number): string {
  return `${value.toFixed(2)}%`;
}

function formatUsd(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

function RateTable({
  title,
  rows,
}: {
  title: string;
  rows: Array<{ label: string; value: string }>;
}) {
  return (
    <section className="border border-border bg-surface px-4 py-5">
      <h4 className="text-sm font-semibold text-foreground">{title}</h4>
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

export function OpsDashboard() {
  const snapshot = buildOpsDashboardSnapshot();

  return (
    <div className="flex flex-col gap-8">
      <section className="rounded-lg border border-border bg-surface px-6 py-8">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">
          Operations dashboard
        </p>
        <h2 className="mt-2 font-display text-3xl tracking-tight text-foreground">
          Milestone 2 business logic
        </h2>
        <p className="mt-3 max-w-2xl text-base leading-7 text-muted">
          Results from the shared <code className="text-foreground">healthcore-testing</code>{" "}
          package — denial rates, no-show cost estimates, and CME compliance — rendered
          here instead of the terminal console.
        </p>
        <p className="mt-2 text-xs text-muted">
          Snapshot generated {new Date(snapshot.generatedAt).toLocaleString()} · sample data
          only
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <div className="border border-border bg-surface px-4 py-5">
          <p className="text-xs uppercase tracking-[0.14em] text-muted">Claims reviewed</p>
          <p className="mt-2 font-display text-3xl text-foreground">
            {snapshot.claims.total}
          </p>
          <p className="mt-1 text-sm text-muted">
            {snapshot.claims.denied.length} denied in sample set
          </p>
        </div>
        <div className="border border-border bg-surface px-4 py-5">
          <p className="text-xs uppercase tracking-[0.14em] text-muted">High-denial payers</p>
          <p className="mt-2 font-display text-3xl text-foreground">
            {snapshot.claims.highDenialPayers.length}
          </p>
          <p className="mt-1 text-sm text-muted">
            {snapshot.claims.highDenialPayers.join(", ") || "None above threshold"}
          </p>
        </div>
        <div className="border border-border bg-surface px-4 py-5">
          <p className="text-xs uppercase tracking-[0.14em] text-muted">High no-show clinics</p>
          <p className="mt-2 font-display text-3xl text-foreground">
            {snapshot.noShows.highNoShowLocations.length}
          </p>
          <p className="mt-1 text-sm text-muted">
            {snapshot.noShows.highNoShowLocations.join(", ") || "None above threshold"}
          </p>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <RateTable
          title="Denial rate by payer"
          rows={Object.entries(snapshot.claims.denialRatesByPayer).map(
            ([label, value]) => ({
              label,
              value: formatPercent(value),
            })
          )}
        />
        <RateTable
          title="Denial rate by location"
          rows={Object.entries(snapshot.claims.denialRatesByLocation).map(
            ([label, value]) => ({
              label,
              value: formatPercent(value),
            })
          )}
        />
      </section>

      <section className="border border-border bg-surface px-4 py-5">
        <h4 className="text-sm font-semibold text-foreground">
          No-show weekly cost estimate
        </h4>
        <p className="mt-1 text-sm text-muted">
          Week ending {snapshot.noShows.weeklyCosts[0]?.weekEndingDate ?? "—"}
        </p>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[32rem] text-left text-sm">
            <thead className="border-b border-panel-line text-muted">
              <tr>
                <th className="py-2 pr-4 font-medium">Location</th>
                <th className="py-2 pr-4 font-medium">No-show rate</th>
                <th className="py-2 font-medium">Est. lost revenue</th>
              </tr>
            </thead>
            <tbody>
              {snapshot.noShows.weeklyCosts.map((row) => (
                <tr key={row.locationId} className="border-b border-panel-line/80">
                  <td className="py-3 pr-4 text-foreground">
                    <div>{row.locationName}</div>
                    <div className="text-xs text-muted">{row.locationId}</div>
                  </td>
                  <td className="py-3 pr-4 text-foreground">
                    {formatPercent(row.noShowRate)}
                  </td>
                  <td className="py-3 font-medium text-foreground">
                    {formatUsd(row.noShowCostUsd)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="border border-border bg-surface px-4 py-5">
          <h4 className="text-sm font-semibold text-foreground">
            CME at risk · as of {snapshot.cme.asOfDate}
          </h4>
          {snapshot.cme.atRisk.length === 0 ? (
            <p className="mt-4 text-sm text-muted">No clinicians currently at risk.</p>
          ) : (
            <ul className="mt-4 divide-y divide-panel-line">
              {snapshot.cme.atRisk.map((report) => (
                <li key={report.clinicianId} className="py-3 text-sm">
                  <p className="font-medium text-foreground">{report.fullName}</p>
                  <p className="text-muted">
                    {report.role} · {report.locationId} · {report.percentComplete}% complete ·{" "}
                    {report.hoursRemaining} hrs remaining
                  </p>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="border border-border bg-surface px-4 py-5">
          <h4 className="text-sm font-semibold text-foreground">
            CME overdue · as of {snapshot.cme.asOfDate}
          </h4>
          {snapshot.cme.overdue.length === 0 ? (
            <p className="mt-4 text-sm text-muted">No overdue CME records in sample data.</p>
          ) : (
            <ul className="mt-4 divide-y divide-panel-line">
              {snapshot.cme.overdue.map((report) => (
                <li key={report.clinicianId} className="py-3 text-sm">
                  <p className="font-medium text-foreground">{report.fullName}</p>
                  <p className="text-muted">
                    {report.role} · {report.locationId} · {report.hoursLogged}/
                    {report.hoursRequired} hrs
                  </p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <section className="border border-border bg-surface px-4 py-5">
        <h4 className="text-sm font-semibold text-foreground">Denied claims (filtered)</h4>
        <ul className="mt-4 divide-y divide-panel-line">
          {snapshot.claims.denied.map((claim) => (
            <li
              key={claim.claimId}
              className="flex flex-wrap items-center justify-between gap-2 py-3 text-sm"
            >
              <span className="font-medium text-foreground">{claim.claimId}</span>
              <span className="text-muted">
                {claim.payerName} · {claim.locationId} · {formatUsd(claim.claimAmount)}
              </span>
              <span className="text-foreground">{claim.denialReason ?? "unspecified"}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
