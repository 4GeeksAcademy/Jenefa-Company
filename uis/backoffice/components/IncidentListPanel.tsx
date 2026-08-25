"use client";

import { useCallback, useMemo, useState } from "react";
import {
  INCIDENT_BRANCHES,
  INCIDENT_ORIGINS,
  INCIDENT_STATUSES,
  listIncidents,
  updateIncidentStatus,
  type Incident,
  type IncidentBranch,
  type IncidentOrigin,
  type IncidentStatus,
} from "@/lib/incidentApi";
import { BRANCH_LABELS, ORIGIN_LABELS, STATUS_LABELS } from "@/lib/incidentLabels";

type Filters = {
  status: IncidentStatus | "";
  origin: IncidentOrigin | "";
  branch: IncidentBranch | "";
};

const INITIAL_FILTERS: Filters = {
  status: "",
  origin: "",
  branch: "",
};

export function IncidentListPanel({
  initialItems,
  initialError = null,
}: {
  initialItems: Incident[];
  initialError?: string | null;
}) {
  const [filters, setFilters] = useState<Filters>(INITIAL_FILTERS);
  const [items, setItems] = useState<Incident[] | null>(initialItems);
  const [fetchError, setFetchError] = useState<string | null>(initialError);
  const [isLoading, setIsLoading] = useState(false);
  const [pendingStatusById, setPendingStatusById] = useState<Record<number, boolean>>({});
  const [actionError, setActionError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const result = await listIncidents(filters);
      setItems(result.items);
      setFetchError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to load incidents.";
      setFetchError(message);
      setItems([]);
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  const hasData = (items?.length ?? 0) > 0;

  const ordered = useMemo(
    () => (items ?? []).slice().sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at)),
    [items]
  );

  async function onChangeStatus(incidentId: number, nextStatus: IncidentStatus) {
    setActionError(null);
    const previous = items ?? [];

    setItems((current) =>
      current.map((incident) =>
        incident.id === incidentId ? { ...incident, status: nextStatus } : incident
      )
    );
    setPendingStatusById((prev) => ({ ...prev, [incidentId]: true }));

    try {
      const updated = await updateIncidentStatus(incidentId, nextStatus);
      setItems((current) =>
        current.map((incident) => (incident.id === incidentId ? updated : incident))
      );
    } catch (err) {
      setItems(previous);
      const message = err instanceof Error ? err.message : "Status update failed.";
      setActionError(message);
    } finally {
      setPendingStatusById((prev) => ({ ...prev, [incidentId]: false }));
    }
  }

  return (
    <section className="border border-border bg-surface px-6 py-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="font-display text-2xl text-foreground">Incident list</h2>
          <p className="mt-2 text-sm text-muted">
            Filter incidents and update lifecycle status inline.
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            setItems(null);
            setFetchError(null);
            void load();
          }}
          className="border border-border bg-white px-3 py-2 text-sm text-foreground hover:bg-background"
        >
          Refresh
        </button>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <label className="text-sm text-foreground">
          Status
          <select
            className="mt-1 w-full border border-border bg-white px-3 py-2 text-sm"
            value={filters.status}
            onChange={(e) => {
              setItems(null);
              setFetchError(null);
              setFilters((prev) => ({
                ...prev,
                status: e.target.value as Filters["status"],
              }));
            }}
          >
            <option value="">All statuses</option>
            {INCIDENT_STATUSES.map((value) => (
              <option key={value} value={value}>
                {STATUS_LABELS[value]}
              </option>
            ))}
          </select>
        </label>

        <label className="text-sm text-foreground">
          Origin
          <select
            className="mt-1 w-full border border-border bg-white px-3 py-2 text-sm"
            value={filters.origin}
            onChange={(e) => {
              setItems(null);
              setFetchError(null);
              setFilters((prev) => ({
                ...prev,
                origin: e.target.value as Filters["origin"],
              }));
            }}
          >
            <option value="">All origins</option>
            {INCIDENT_ORIGINS.map((value) => (
              <option key={value} value={value}>
                {ORIGIN_LABELS[value]}
              </option>
            ))}
          </select>
        </label>

        <label className="text-sm text-foreground">
          Branch
          <select
            className="mt-1 w-full border border-border bg-white px-3 py-2 text-sm"
            value={filters.branch}
            onChange={(e) => {
              setItems(null);
              setFetchError(null);
              setFilters((prev) => ({
                ...prev,
                branch: e.target.value as Filters["branch"],
              }));
            }}
          >
            <option value="">All branches</option>
            {INCIDENT_BRANCHES.map((value) => (
              <option key={value} value={value}>
                {BRANCH_LABELS[value]}
              </option>
            ))}
          </select>
        </label>
      </div>

      {fetchError ? (
        <div className="mt-5 border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900">
          <p className="font-semibold">Incident list could not be loaded.</p>
          <p className="mt-1">{fetchError}</p>
          <button
            type="button"
            onClick={() => {
              setItems(null);
              setFetchError(null);
              void load();
            }}
            className="mt-3 border border-red-400 bg-white px-3 py-2 text-sm"
          >
            Retry
          </button>
        </div>
      ) : null}

      {actionError ? (
        <div className="mt-5 border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          {actionError}
        </div>
      ) : null}

      {isLoading ? (
        <p className="mt-6 text-sm text-muted">Loading incidents...</p>
      ) : null}

      {!isLoading && !fetchError && !hasData ? (
        <p className="mt-6 text-sm text-muted">
          No incidents match the selected filters.
        </p>
      ) : null}

      {!isLoading && !fetchError && hasData ? (
        <div className="mt-6 overflow-x-auto">
          <table className="w-full min-w-[56rem] text-left text-sm">
            <thead className="border-b border-panel-line text-muted">
              <tr>
                <th className="py-2 pr-3 font-medium">ID</th>
                <th className="py-2 pr-3 font-medium">Title</th>
                <th className="py-2 pr-3 font-medium">Origin</th>
                <th className="py-2 pr-3 font-medium">Branch</th>
                <th className="py-2 pr-3 font-medium">Status</th>
                <th className="py-2 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {ordered.map((incident) => (
                <tr key={incident.id} className="border-b border-panel-line/80 align-top">
                  <td className="py-3 pr-3 font-medium text-foreground">#{incident.id}</td>
                  <td className="py-3 pr-3 text-foreground">
                    <p>{incident.title}</p>
                    <p className="mt-1 max-w-[28rem] text-xs text-muted">
                      {incident.description}
                    </p>
                  </td>
                  <td className="py-3 pr-3 text-foreground">
                    {ORIGIN_LABELS[incident.origin]}
                  </td>
                  <td className="py-3 pr-3 text-foreground">
                    {BRANCH_LABELS[incident.branch]}
                  </td>
                  <td className="py-3 pr-3 text-foreground">
                    <select
                      className="border border-border bg-white px-2 py-1 text-sm"
                      value={incident.status}
                      disabled={pendingStatusById[incident.id] === true}
                      onChange={(e) =>
                        void onChangeStatus(
                          incident.id,
                          e.target.value as IncidentStatus
                        )
                      }
                    >
                      {INCIDENT_STATUSES.map((value) => (
                        <option key={value} value={value}>
                          {STATUS_LABELS[value]}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="py-3 text-foreground">
                    {new Date(incident.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}
