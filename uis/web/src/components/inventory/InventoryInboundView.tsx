"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  fetchProducts,
  recordInbound,
  type MedicalSupplyRead,
} from "@/lib/inventory";
import { toUserFacingMessage } from "@/lib/userFacingError";
import { useRequireAuth } from "@/lib/useRequireAuth";
import { InventorySubnav } from "@/components/inventory/InventorySubnav";

const inputClass =
  "mt-1 w-full border border-border bg-background px-3 py-2 text-sm text-foreground";
const labelClass = "block text-xs font-semibold uppercase tracking-[0.12em] text-muted";

export function InventoryInboundView() {
  const { isAuthorized } = useRequireAuth();
  const [products, setProducts] = useState<MedicalSupplyRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [selectedItem, setSelectedItem] = useState("");
  const [quantity, setQuantity] = useState("");
  const [clinicId, setClinicId] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthorized) {
      return;
    }

    void fetchProducts()
      .then((rows) => {
        setProducts(rows);
        const requestedItem = new URLSearchParams(window.location.search).get("item");
        if (requestedItem && rows.some((row) => String(row.id) === requestedItem)) {
          setSelectedItem(requestedItem);
        }
      })
      .catch((err: unknown) => setError(toUserFacingMessage(err)))
      .finally(() => setLoading(false));
  }, [isAuthorized]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setStatus(null);

    try {
      await recordInbound({
        medical_supply_id: Number(selectedItem),
        quantity: Number(quantity),
        clinic_id: clinicId.trim(),
      });
      setSelectedItem("");
      setQuantity("");
      setClinicId("");
      setStatus("Inbound delivery was successfully logged.");
    } catch (err: unknown) {
      setError(toUserFacingMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  if (!isAuthorized) {
    return null;
  }

  return (
    <section className="space-y-6">
      <header className="space-y-3 rounded-lg border border-border bg-surface px-6 py-6">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">
          Backoffice inventory
        </p>
        <h2 className="font-display text-3xl tracking-tight text-foreground">
          Inbound Inventory Intake
        </h2>
        <p className="text-sm leading-7 text-muted">
          Log inbound clinic deliveries using catalog-backed item selection.
        </p>
        <InventorySubnav />
      </header>

      {status ? (
        <div role="status" className="border border-green-300 bg-green-50 px-4 py-3 text-sm text-green-900">
          {status}
        </div>
      ) : null}
      {error ? (
        <div role="alert" className="border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900">
          <p className="font-semibold">Inbound request failed</p>
          <p className="mt-1">{error}</p>
        </div>
      ) : null}

      <form onSubmit={(event) => void onSubmit(event)} className="rounded-lg border border-border bg-surface px-6 py-6">
        <label className={labelClass}>
          Select Target Item
          <select
            className={inputClass}
            value={selectedItem}
            onChange={(event) => setSelectedItem(event.target.value)}
            required
            disabled={loading || submitting}
          >
            <option value="">Choose a clinical item</option>
            {products.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name} ({item.sku})
              </option>
            ))}
          </select>
        </label>

        <label className={`${labelClass} mt-4`}>
          Transaction Volume
          <input
            className={inputClass}
            type="number"
            min={1}
            required
            value={quantity}
            onChange={(event) => setQuantity(event.target.value)}
            disabled={submitting}
          />
        </label>

        <label className={`${labelClass} mt-4`}>
          Clinic ID
          <input
            className={inputClass}
            required
            value={clinicId}
            onChange={(event) => setClinicId(event.target.value)}
            placeholder="CLINIC-TX-01"
            disabled={submitting}
          />
        </label>

        <button
          type="submit"
          className="mt-5 bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-sidebar-hover disabled:opacity-60"
          disabled={submitting || loading}
        >
          {submitting ? "Submitting…" : "Record inbound delivery"}
        </button>
      </form>
    </section>
  );
}
