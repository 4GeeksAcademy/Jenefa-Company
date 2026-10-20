"use client";

import { useCallback, useEffect, useState } from "react";

import { ReportingRefresh } from "@/components/ReportingRefresh";
import { fetchExecutiveKpis, flowerMonitorUrl, summarizeExecutiveKpis, type ExecutiveKpi } from "@/lib/reporting";

const KPI_REFRESH_MS = 15000;

function percent(value: number | null) {
  return value === null ? "-" : `${(value * 100).toFixed(1)}%`;
}

export default function ReportingPage() {
  const [rows, setRows] = useState<ExecutiveKpi[]>([]);
  const [error, setError] = useState("");
  const [flowerUrl, setFlowerUrl] = useState("http://localhost:5555");

  const loadKpis = useCallback(async () => {
    try {
      setRows(await fetchExecutiveKpis());
      setError("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to load reporting data.");
    }
  }, []);

  useEffect(() => {
    setFlowerUrl(flowerMonitorUrl());
    void loadKpis();
    const timer = setInterval(() => void loadKpis(), KPI_REFRESH_MS);
    return () => clearInterval(timer);
  }, [loadKpis]);

  const summary = summarizeExecutiveKpis(rows);
  const period = summary.period ? new Date(summary.period).toLocaleDateString() : "No completed run yet";

  return (
    <div className="mx-auto w-full max-w-6xl">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Business logic</p>
          <h1 className="mt-2 font-display text-4xl text-foreground">Business reporting</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">Executive performance across appointment access and claims activity.</p>
          <p className="mt-2 text-sm text-muted">
            Background jobs (Celery, Redis):{" "}
            <a href={flowerUrl} target="_blank" rel="noreferrer" className="font-medium text-accent underline">
              Open Flower monitor
            </a>
          </p>
        </div>
        <ReportingRefresh onCompleted={loadKpis} />
      </div>
      {error ? <p role="alert" className="mt-6 border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900">Reporting data unavailable: {error}</p> : null}
      <section aria-label="Reporting summary" className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          ["Reporting period", period],
          ["Network appointments", summary.totalAppointments.toLocaleString()],
          ["Average no-show rate", percent(summary.averageNoShow)],
          ["Average denial rate", percent(summary.averageDenial)],
        ].map(([label, value]) => (
          <article key={label} className="border border-border bg-surface p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">{label}</p>
            <p className="mt-3 font-display text-3xl text-foreground">{value}</p>
          </article>
        ))}
      </section>
      <section className="mt-8 overflow-x-auto border border-border bg-surface">
        <table className="w-full min-w-[700px] text-left text-sm">
          <thead className="border-b border-border text-xs uppercase tracking-[0.1em] text-muted">
            <tr>{["Clinic", "Region", "Appointments", "No-show", "Denial", "Net settled"].map((heading) => <th key={heading} className="px-5 py-4">{heading}</th>)}</tr>
          </thead>
          <tbody>
            {rows.length ? rows.map((row) => (
              <tr key={`${row.reporting_window_timestamp}-${row.clinic_location_id}`} className="border-b border-border last:border-0">
                <td className="px-5 py-4 font-medium">{row.clinic_location_id}</td>
                <td className="px-5 py-4 text-muted">{row.market_region}</td>
                <td className="px-5 py-4">{row.network_appointment_volume ?? "-"}</td>
                <td className="px-5 py-4">{percent(row.global_no_show_rate)}</td>
                <td className="px-5 py-4">{percent(row.claims_denial_rate)}</td>
                <td className="px-5 py-4">{row.revenue_net_settled === null ? "-" : `${row.revenue_currency ?? ""} ${row.revenue_net_settled.toFixed(2)}`}</td>
              </tr>
            )) : <tr><td colSpan={6} className="px-5 py-6 text-muted">No completed reporting rows are available.</td></tr>}
          </tbody>
        </table>
      </section>
    </div>
  );
}