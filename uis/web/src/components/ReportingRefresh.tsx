"use client";

import { useEffect, useRef, useState } from "react";
import { apiFetch, readJson } from "@/lib/api";

const POLL_INTERVAL_MS = 2000;
const MAX_POLLS = 60;

type RefreshState = { phase: "idle" | "running" | "done" | "error"; message: string };

// 1. Data Type mapping precisely with your project's verified database table schema
type ExecutiveKPIData = {
  id: number;
  reporting_window_timestamp: string;
  clinic_location_id: string;
  market_region: string;
  network_appointment_volume: number | null;
  global_no_show_rate: number | null;
  claims_denial_rate: number | null;
  revenue_currency: string | null;
  revenue_net_settled: number | null;
  patient_satisfaction_score: number | null;
};

export function ReportingRefresh({ onCompleted }: { onCompleted?: () => void | Promise<void> }) {
  const [state, setState] = useState<RefreshState>({ phase: "idle", message: "" });
  const [reportData, setReportData] = useState<ExecutiveKPIData[]>([]);
  const [currentMonth, setCurrentMonth] = useState<string>("No completed run");
  const [selectedClinic, setSelectedClinic] = useState("");
  const [isLoadingData, setIsLoadingData] = useState<boolean>(true);
  
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 2. Fetcher module pulling rows from your active backend router endpoint
  async function fetchReportingData() {
    try {
      setIsLoadingData(true);
      const response = await apiFetch("/services/reporting/kpis"); 
      const data = await readJson<ExecutiveKPIData[]>(response);
      
      if (Array.isArray(data)) {
        setReportData(data);
        if (data.length > 0 && data[0].reporting_window_timestamp) {
          setCurrentMonth(data[0].reporting_window_timestamp.slice(0, 10));
        }
      }
    } catch (err) {
      console.error("Failed to load aggregated performance metrics:", err);
    } finally {
      setIsLoadingData(false);
    }
  }

  const activePeriod = reportData[0]?.reporting_window_timestamp.slice(0, 10) ?? "";
  const activeRows = reportData.filter((row) => row.reporting_window_timestamp.slice(0, 10) === activePeriod);
  const clinicOptions = Array.from(new Set(activeRows.map((row) => row.clinic_location_id))).sort();
  const selectedRow = activeRows.find((row) => row.clinic_location_id === selectedClinic) ?? activeRows[0];
  const totalAppointments = activeRows.reduce((sum, row) => sum + (row.network_appointment_volume ?? 0), 0);
  const average = (values: Array<number | null>) => {
    const present = values.filter((value): value is number => value !== null);
    return present.length ? present.reduce((sum, value) => sum + value, 0) / present.length : null;
  };
  const overallNoShow = average(activeRows.map((row) => row.global_no_show_rate));
  const overallDenial = average(activeRows.map((row) => row.claims_denial_rate));
  const claimsByCurrency = activeRows.reduce<Record<string, number>>((totals, row) => {
    if (row.revenue_net_settled === null) return totals;
    const currency = row.revenue_currency ?? "Unknown currency";
    totals[currency] = (totals[currency] ?? 0) + row.revenue_net_settled;
    return totals;
  }, {});
  const totalClaims = Object.entries(claimsByCurrency)
    .map(([currency, amount]) => `${currency} ${amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}`)
    .join(" · ") || "-";
  const percent = (value: number | null) => value === null ? "-" : `${(value * 100).toFixed(1)}%`;

  useEffect(() => {
    fetchReportingData();

    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, []);

  // 3. Celery / Redis tracking state monitor loop
  async function pollRun(taskId: string, attempt: number) {
    try {
      const response = await apiFetch(`/services/reporting/trigger/${taskId}`);
      const body = await readJson<{ status: string }>(response);
      
      if (body.status === "success" || body.status === "SUCCESS") {
        setState({ phase: "done", message: "Reporting run completed successfully!" });
        await fetchReportingData();
        await onCompleted?.();
        return;
      }
      if (body.status === "failure" || body.status === "FAILURE") {
        setState({ phase: "error", message: "Reporting run failed. Verify your Celery worker console logs." });
        return;
      }
      if (attempt >= MAX_POLLS) {
        setState({ phase: "error", message: "Run is taking longer than expected. Check back soon." });
        return;
      }
      setState({ phase: "running", message: `Aggregating database summaries (Status: ${body.status})…` });
      timer.current = setTimeout(() => void pollRun(taskId, attempt + 1), POLL_INTERVAL_MS);
    } catch (cause) {
      setState({
        phase: "error",
        message: cause instanceof Error ? cause.message : "Unable to verify run task status.",
      });
    }
  }

  // 4. Ingestion runner pipeline background queue trigger
  async function startRun() {
    setState({ phase: "running", message: "Queuing background task run…" });
    try {
      const response = await apiFetch("/services/reporting/trigger", { method: "POST" });
      const body = await readJson<{ task_id: string; status: string }>(response);
      void pollRun(body.task_id, 1);
    } catch (cause) {
      setState({
        phase: "error",
        message: cause instanceof Error ? cause.message : "Unable to trigger the pipeline run engine.",
      });
    }
  }

  return (
    <div className="space-y-6 w-full">
      {/* Control Action Bar Area */}
      <div className="flex flex-col items-start gap-2 sm:items-end justify-between sm:flex-row">
        <div>
          <h3 className="text-sm text-muted font-medium">
            Active Cycle Period: <span className="font-mono text-foreground font-semibold">{currentMonth}</span>
          </h3>
        </div>
        <div className="flex flex-wrap items-end justify-end gap-3">
          {clinicOptions.length ? (
            <label className="text-right text-xs font-semibold uppercase tracking-wide text-muted">
              Clinic location
              <select
                value={selectedClinic || clinicOptions[0]}
                onChange={(event) => setSelectedClinic(event.target.value)}
                className="mt-1 block border border-border bg-surface px-3 py-2 text-sm font-normal normal-case tracking-normal text-foreground"
              >
                {clinicOptions.map((clinic) => <option key={clinic} value={clinic}>{clinic}</option>)}
              </select>
            </label>
          ) : null}
          <div className="flex flex-col items-end gap-1">
          <button
            type="button"
            onClick={() => void startRun()}
            disabled={state.phase === "running"}
            className="border border-border bg-surface px-4 py-2 text-sm font-medium text-foreground hover:bg-panel-line/40 disabled:opacity-60 rounded shadow-sm transition-colors"
          >
            {state.phase === "running" ? "Running Core Pipeline…" : "Refresh Reporting Data"}
          </button>
          {state.message ? (
            <p role="status" className={state.phase === "error" ? "text-sm text-red-600 font-medium" : "text-sm text-muted"}>
              {state.message}
            </p>
          ) : null}
          </div>
        </div>
      </div>

      <section aria-label="Reporting totals" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          ["Network appointments", totalAppointments.toLocaleString()],
          ["Overall no-show rate", percent(overallNoShow)],
          ["Overall denial rate", percent(overallDenial)],
          ["Total net settled", totalClaims],
        ].map(([label, value]) => (
          <article key={label} className="border border-border bg-surface p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">{label}</p>
            <p className="mt-3 font-display text-3xl text-foreground">{value}</p>
          </article>
        ))}
      </section>

      {selectedRow ? (
        <section aria-label="Selected clinic reporting" className="border border-border bg-surface p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Selected clinic</p>
          <h2 className="mt-2 font-display text-2xl text-foreground">{selectedRow.clinic_location_id}</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-4">
            <div><p className="text-xs text-muted">Reporting period</p><p className="mt-1 font-medium">{selectedRow.reporting_window_timestamp.slice(0, 10)}</p></div>
            <div><p className="text-xs text-muted">No-show rate</p><p className="mt-1 font-medium">{percent(selectedRow.global_no_show_rate)}</p></div>
            <div><p className="text-xs text-muted">Denial rate</p><p className="mt-1 font-medium">{percent(selectedRow.claims_denial_rate)}</p></div>
            <div><p className="text-xs text-muted">Net settled</p><p className="mt-1 font-medium">{selectedRow.revenue_net_settled === null ? "-" : `${selectedRow.revenue_currency ?? ""} ${selectedRow.revenue_net_settled.toLocaleString(undefined, { minimumFractionDigits: 2 })}`}</p></div>
          </div>
        </section>
      ) : null}

      {/* Main Metric Table Output Display */}
      <div className="border border-border bg-surface p-6 rounded-md shadow-sm">
        <h2 className="text-md font-semibold text-foreground mb-4">Executive Network Performance Summary</h2>
        
        {isLoadingData ? (
          <p className="text-sm text-muted">Retrieving metrics from Supabase database tables...</p>
        ) : reportData.length === 0 ? (
          <p className="text-sm text-muted">No telemetry records processed for this cycle yet. Trigger a sync run above.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-border text-muted font-medium">
                  <th className="pb-2">Clinic ID</th>
                  <th className="pb-2">Region</th>
                  <th className="pb-2 text-right">Appointments</th>
                  <th className="pb-2 text-right">No-Show Rate</th>
                  <th className="pb-2 text-right">Claims Denial Rate</th>
                  <th className="pb-2 text-right">Net Settled</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-foreground">
                {reportData.map((row, idx) => (
                  <tr key={`${row.reporting_window_timestamp}-${row.clinic_location_id}-${row.id || idx}`} className="hover:bg-panel-line/10 transition-colors">
                    <td className="py-3 font-medium text-foreground">
                      {row.clinic_location_id}
                    </td>
                    <td className="py-3 text-xs uppercase tracking-wider text-muted font-semibold">
                      {row.market_region || "GLOBAL"}
                    </td>
                    <td className="py-3 text-right font-mono font-medium text-foreground">
                      {row.network_appointment_volume !== null ? `${row.network_appointment_volume} visits` : "—"}
                    </td>
                    <td className="py-3 text-right">
                      <span className={`px-2 py-0.5 text-xs rounded font-medium ${row.global_no_show_rate !== null && row.global_no_show_rate > 0.2 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                        {percent(row.global_no_show_rate)}
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <span className={`px-2 py-0.5 text-xs rounded font-medium ${row.claims_denial_rate !== null && row.claims_denial_rate > 0.08 ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-700'}`}>
                        {row.claims_denial_rate !== null ? `${(Number(row.claims_denial_rate) * 100).toFixed(1)}%` : "—"}
                      </span>
                    </td>
                    <td className="py-3 text-right font-mono font-medium text-muted">
                      {row.revenue_net_settled !== null ? `${row.revenue_currency || "$"}${Number(row.revenue_net_settled).toLocaleString()}` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
