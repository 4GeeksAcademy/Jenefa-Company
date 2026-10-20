"use client";

import { useEffect, useState } from "react";
import { apiFetch, readJson } from "@/lib/api";
import { fetchOrders, fetchProducts, type MedicalSupplyRead, type OrderRead } from "@/lib/inventory";
import {
  fetchIncidentHistory,
  fetchLatestIncidentAnalysis,
  type IncidentAnalysis,
  type IncidentRun,
} from "@/lib/incidentApi";
import { IncidentResults } from "@/components/IncidentResults";

type RfpTicket = {
  ticket_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  metrics?: Record<string, number>;
};

type SourceKey = "inventory" | "orders" | "incidents" | "rfp";

const SOURCE_LABELS: Record<SourceKey, string> = {
  inventory: "inventory",
  orders: "inventory ledger",
  incidents: "incident history",
  rfp: "RFP intake",
};

function errorMessage(reason: unknown): string {
  return reason instanceof Error ? reason.message : "Unavailable";
}

function formatTime(value: string): string {
  return new Date(value).toLocaleString();
}

function DataTable({
  title,
  headers,
  rows,
  error,
  emptyMessage,
}: {
  title: string;
  headers: string[];
  rows: string[][];
  error: string | null;
  emptyMessage: string;
}) {
  return (
    <section className="overflow-x-auto rounded-lg border border-slate-200 bg-white p-6">
      <h2 className="mb-4 text-xl font-normal">{title}</h2>
      {error ? (
        <p className="text-sm text-red-900">{error}</p>
      ) : rows.length === 0 ? (
        <p className="text-sm text-slate-500">{emptyMessage}</p>
      ) : (
        <table className="w-full min-w-[680px] border-collapse text-sm">
          <thead>
            <tr>
              {headers.map((header) => (
                <th key={header} className="border-b border-slate-200 pb-3 pr-3 text-left text-xs uppercase tracking-wide text-slate-500">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={`${title}-${rowIndex}`}>
                {row.map((cell, index) => (
                  <td key={`${rowIndex}-${index}`} className={`border-b border-slate-200 py-3 pr-3 ${index === 0 ? "font-bold text-slate-900" : "text-slate-500"}`}>
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

export function OperationsLedger() {
  const [apiStatus, setApiStatus] = useState("Loading live data");
  const [lastRefresh, setLastRefresh] = useState("");
  const [products, setProducts] = useState<MedicalSupplyRead[]>([]);
  const [orders, setOrders] = useState<OrderRead[]>([]);
  const [incidentRuns, setIncidentRuns] = useState<IncidentRun[]>([]);
  const [incidentRetentionDays, setIncidentRetentionDays] = useState(10);
  const [latestAnalysis, setLatestAnalysis] = useState<IncidentAnalysis | null>(null);
  const [tickets, setTickets] = useState<RfpTicket[]>([]);
  const [sourceErrors, setSourceErrors] = useState<Record<SourceKey, string | null>>({
    inventory: null,
    orders: null,
    incidents: null,
    rfp: null,
  });

  useEffect(() => {
    let active = true;
    let timer: number | undefined;
    const refresh = async () => {
      const [productsResult, ordersResult, incidentsResult, ticketsResult, latestResult] = await Promise.allSettled([
        fetchProducts(),
        fetchOrders(),
        fetchIncidentHistory(),
        apiFetch("/rfp/tickets", { cache: "no-store" }).then((response) => readJson<RfpTicket[]>(response)),
        fetchLatestIncidentAnalysis(),
      ]);
      if (!active) return;

      const failures: Record<SourceKey, string | null> = {
        inventory: productsResult.status === "rejected" ? errorMessage(productsResult.reason) : null,
        orders: ordersResult.status === "rejected" ? errorMessage(ordersResult.reason) : null,
        incidents: incidentsResult.status === "rejected" ? errorMessage(incidentsResult.reason) : null,
        rfp: ticketsResult.status === "rejected" ? errorMessage(ticketsResult.reason) : null,
      };
      setSourceErrors(failures);
      setProducts(productsResult.status === "fulfilled" ? productsResult.value : []);
      setOrders(ordersResult.status === "fulfilled" ? ordersResult.value : []);
      if (incidentsResult.status === "fulfilled") {
        setIncidentRuns(incidentsResult.value.items);
        setIncidentRetentionDays(incidentsResult.value.retention_days);
      } else {
        setIncidentRuns([]);
      }
      if (latestResult.status === "fulfilled") setLatestAnalysis(latestResult.value);
      setTickets(ticketsResult.status === "fulfilled" ? ticketsResult.value : []);

      const failedCount = Object.values(failures).filter(Boolean).length;
      if (failedCount === 0) setApiStatus("Live");
      else if (failedCount === Object.keys(failures).length) setApiStatus("Offline - no live data available");
      else setApiStatus(`Partial - ${Object.entries(failures).filter(([, error]) => error).map(([key]) => SOURCE_LABELS[key as SourceKey]).join(", ")} unavailable`);
      setLastRefresh(new Date().toLocaleTimeString());
    };
    const start = async () => {
      await refresh();
      if (active) timer = window.setInterval(refresh, 30000);
    };
    void start();
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  const stockUnits = products.reduce((sum, product) => sum + product.current_stock, 0);
  const clinicCount = new Set(products.map((product) => product.clinic_id)).size;
  const metrics = [
    { label: "Inventory SKUs", value: String(products.length), note: `${clinicCount} clinic partition${clinicCount === 1 ? "" : "s"}` },
    { label: "Units on hand", value: stockUnits.toLocaleString(), note: "Sum of current stock" },
    { label: "Incident analyses", value: String(incidentRuns.length), note: `Metadata kept ${incidentRetentionDays} days` },
    { label: "RFP tickets", value: String(tickets.length), note: "Most recent 100" },
  ];

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-lg font-bold uppercase tracking-widest text-slate-500">Knowledge base</p>
          <h1 className="mt-2 text-lg font-normal">Operations Overview</h1>
        </div>
        <p className="text-sm text-slate-500">
          {apiStatus}
          {lastRefresh ? ` · ${lastRefresh}` : ""}
        </p>
      </header>

      <section aria-label="Operational summary" className="grid grid-cols-[repeat(auto-fit,minmax(190px,1fr))] gap-4">
        {metrics.map((metric) => (
          <article key={metric.label} className="rounded-lg border border-slate-200 bg-white p-5">
            <div className="text-xs font-bold uppercase tracking-wide text-slate-500">{metric.label}</div>
            <div className="mt-3 text-3xl font-normal">{metric.value}</div>
            <div className="mt-1 text-xs text-slate-500">{metric.note}</div>
          </article>
        ))}
      </section>

      <section aria-label="Latest incident analysis" className="flex flex-col gap-4">
        <h2 className="text-xl font-normal">Latest incident analysis</h2>
        {latestAnalysis ? (
          <IncidentResults result={latestAnalysis} />
        ) : (
          <p className="text-sm text-slate-500">No incident analysis uploaded yet. Upload a CSV on the Incidents Analysis page.</p>
        )}
      </section>

      <DataTable
        title="Inventory ledger"
        headers={["Order ID", "Type", "Product", "Clinic", "Quantity", "Recorded"]}
        rows={orders.map((order) => [
          String(order.id),
          order.kind,
          order.medical_supply.name,
          order.clinic_id,
          String(order.quantity),
          formatTime(order.created_at),
        ])}
        error={sourceErrors.orders}
        emptyMessage="No inventory movements recorded yet."
      />
      <DataTable
        title="Incident analysis history"
        headers={["Run ID", "Valid / total records", "Analysed"]}
        rows={incidentRuns.map((run) => [run.id, `${run.valid_records} / ${run.total_records}`, formatTime(run.created_at)])}
        error={sourceErrors.incidents}
        emptyMessage={`No incident analyses in the last ${incidentRetentionDays} days.`}
      />
      <DataTable
        title="RFP intake history"
        headers={["Ticket ID", "Status", "Words", "Estimated tokens", "Created", "Last updated"]}
        rows={tickets.map((ticket) => [
          ticket.ticket_id,
          ticket.status,
          String(ticket.metrics?.word_count ?? "-"),
          String(ticket.metrics?.estimated_tokens ?? "-"),
          formatTime(ticket.created_at),
          formatTime(ticket.updated_at),
        ])}
        error={sourceErrors.rfp}
        emptyMessage="No RFP tickets yet."
      />
    </div>
  );
}
