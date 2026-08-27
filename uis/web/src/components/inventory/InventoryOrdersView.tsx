"use client";

import { useEffect, useState } from "react";
import { fetchOrders, type OrderRead } from "@/lib/inventory";
import { toUserFacingMessage } from "@/lib/userFacingError";
import { useRequireAuth } from "@/lib/useRequireAuth";
import { InventorySubnav } from "@/components/inventory/InventorySubnav";

function movementLabel(kind: OrderRead["kind"]): string {
  return kind === "inbound" ? "Restock/Replenish" : "Fulfillment/Removal";
}

function timezoneForClinic(clinicId: string): string {
  const normalized = clinicId.toUpperCase();
  if (normalized.includes("-UK-")) {
    return "Europe/London";
  }
  if (normalized.includes("-TX-")) {
    return "America/Chicago";
  }
  if (normalized.includes("-FL-") || normalized.includes("-GA-")) {
    return "America/New_York";
  }
  return "UTC";
}

function formatLoggedTimestamp(isoTimestamp: string, clinicId: string): string {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: timezoneForClinic(clinicId),
    }).format(new Date(isoTimestamp));
  } catch {
    return new Date(isoTimestamp).toLocaleString();
  }
}

export function InventoryOrdersView() {
  const { isAuthorized } = useRequireAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [orders, setOrders] = useState<OrderRead[]>([]);

  useEffect(() => {
    if (!isAuthorized) {
      return;
    }

    void fetchOrders()
      .then((rows) => setOrders(rows))
      .catch((err: unknown) => {
        setError(toUserFacingMessage(err));
      })
      .finally(() => setLoading(false));
  }, [isAuthorized]);

  if (!isAuthorized) {
    return null;
  }

  return (
    <section className="space-y-6">
      <header className="space-y-3 rounded-lg border border-border bg-surface px-6 py-6">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">
          Backoffice inventory
        </p>
        <h2 className="font-display text-3xl tracking-tight text-foreground">Orders History Ledger</h2>
        <p className="text-sm leading-7 text-muted">
          Read-only audit stream of all inbound and outbound inventory movement.
        </p>
        <InventorySubnav />
      </header>

      {error ? (
        <div role="alert" className="border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900">
          <p className="font-semibold">Orders request failed</p>
          <p className="mt-1">{error}</p>
        </div>
      ) : null}

      <div className="overflow-x-auto rounded-lg border border-border bg-surface">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-panel-line text-xs uppercase tracking-[0.12em] text-muted">
              <th className="px-4 py-3">Clinical Item Name</th>
              <th className="px-4 py-3">Transaction Volume</th>
              <th className="px-4 py-3">Movement Class</th>
              <th className="px-4 py-3">Logged Timestamp</th>
              <th className="px-4 py-3">Operator ID</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-panel-line">
            {loading ? (
              <tr>
                <td className="px-4 py-4 text-muted" colSpan={5}>
                  Loading orders…
                </td>
              </tr>
            ) : orders.length === 0 ? (
              <tr>
                <td className="px-4 py-4 text-muted" colSpan={5}>
                  No order history available.
                </td>
              </tr>
            ) : (
              orders.map((row) => {
                const inbound = row.kind === "inbound";
                return (
                  <tr key={`${row.kind}-${row.id}`}>
                    <td className="px-4 py-4 font-semibold text-foreground">{row.medical_supply.name}</td>
                    <td className="px-4 py-4 text-foreground">{row.quantity}</td>
                    <td className="px-4 py-4">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-semibold ${
                          inbound
                            ? "bg-green-100 text-green-900"
                            : "bg-sky-100 text-sky-900"
                        }`}
                      >
                        <span aria-hidden="true">{inbound ? "↑" : "↓"}</span>
                        {movementLabel(row.kind)}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-muted">
                      {formatLoggedTimestamp(row.created_at, row.clinic_id)}
                    </td>
                    <td className="px-4 py-4 font-mono text-xs text-muted">{row.user_uuid}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
