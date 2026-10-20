"use client";

import { FormEvent, useEffect, useState } from "react";
import { ApiRequestError } from "@/lib/api";
import {
  fetchProduct,
  fetchProducts,
  recordOutbound,
  type MedicalSupplyDetail,
  type MedicalSupplyRead,
} from "@/lib/inventory";
import { toUserFacingMessage } from "@/lib/userFacingError";
import { useRequireAuth } from "@/lib/useRequireAuth";
import { InventorySubnav } from "@/components/inventory/InventorySubnav";

const inputClass =
  "mt-1 w-full border border-border bg-background px-3 py-2 text-sm text-foreground";
const labelClass = "block text-xs font-semibold uppercase tracking-[0.12em] text-muted";

export function InventoryOutboundView() {
  const { isAuthorized } = useRequireAuth();
  const [products, setProducts] = useState<MedicalSupplyRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [stockLoading, setStockLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState("");
  const [detail, setDetail] = useState<MedicalSupplyDetail | null>(null);
  const [quantity, setQuantity] = useState("");
  const [clinicId, setClinicId] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [quantityApiError, setQuantityApiError] = useState<string | null>(null);

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

  useEffect(() => {
    if (!selectedItem) {
      return;
    }

    let cancelled = false;
    void fetchProduct(Number(selectedItem))
      .then((loaded) => {
        if (!cancelled) {
          setDetail(loaded);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(toUserFacingMessage(err));
        }
      })
      .finally(() => {
        if (!cancelled) {
          setStockLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedItem]);

  // Stock is checked per clinic partition, matching the backend overdraft rule.
  const availableStock =
    detail && clinicId
      ? (detail.partitions.find((partition) => partition.clinic_id === clinicId)?.current_stock ?? 0)
      : null;

  const quantityWarning =
    quantity &&
    availableStock !== null &&
    Number.isFinite(Number(quantity)) &&
    Number(quantity) > availableStock
      ? "Dispersal amount exceeds current available inventory."
      : null;

  const clinicIds = Array.from(new Set(products.map((item) => item.clinic_id))).sort();

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setStatus(null);
    setQuantityApiError(null);

    const parsedQuantity = Number(quantity);
    if (availableStock !== null && parsedQuantity > availableStock) {
      setSubmitting(false);
      return;
    }

    try {
      const itemId = Number(selectedItem);
      await recordOutbound({
        medical_supply_id: itemId,
        quantity: parsedQuantity,
        clinic_id: clinicId.trim(),
      });
      setQuantity("");
      setClinicId("");
      setStatus("Outbound dispersal was successfully logged.");
      setStockLoading(true);
      await fetchProduct(itemId)
        .then((loaded) => setDetail(loaded))
        .catch((err: unknown) => setError(toUserFacingMessage(err)))
        .finally(() => setStockLoading(false));
    } catch (err: unknown) {
      if (err instanceof ApiRequestError && err.status === 400) {
        setQuantityApiError(err.message);
      } else {
        setError(toUserFacingMessage(err));
      }
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
          Outbound Inventory Dispersal
        </h2>
        <p className="text-sm leading-7 text-muted">
          Outbound movement is guarded by live stock pre-checks and backend validation.
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
          <p className="font-semibold">Outbound request failed</p>
          <p className="mt-1">{error}</p>
        </div>
      ) : null}

      <form onSubmit={(event) => void onSubmit(event)} className="rounded-lg border border-border bg-surface px-6 py-6">
        <label className={labelClass}>
          Select Target Item
          <select
            className={inputClass}
            value={selectedItem}
            onChange={(event) => {
              const nextValue = event.target.value;
              setSelectedItem(nextValue);
              setStockLoading(Boolean(nextValue));
              setDetail(null);
              setQuantityApiError(null);
            }}
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

        <div className="mt-4 rounded-md border border-panel-line bg-background px-3 py-2 text-sm">
          <p className="text-xs uppercase tracking-[0.12em] text-muted">Available Inventory</p>
          <p className="mt-1 font-semibold text-foreground">
            {stockLoading
              ? "Loading current balance…"
              : availableStock !== null
                ? availableStock
                : selectedItem
                  ? "Select a clinic"
                  : "Select an item"}
          </p>
        </div>

        <label className={`${labelClass} mt-4`}>
          Dispersal Amount
          <input
            className={inputClass}
            type="number"
            min={1}
            required
            value={quantity}
            onChange={(event) => setQuantity(event.target.value)}
            disabled={submitting || stockLoading || availableStock === null}
          />
        </label>
        {quantityWarning ? <p className="mt-2 text-sm text-amber-900">{quantityWarning}</p> : null}
        {quantityApiError ? <p className="mt-2 text-sm text-red-800">{quantityApiError}</p> : null}

        <label className={`${labelClass} mt-4`}>
          Clinic ID
          <select
            className={inputClass}
            required
            value={clinicId}
            onChange={(event) => setClinicId(event.target.value)}
            disabled={loading || submitting}
          >
            <option value="">Choose a clinic</option>
            {clinicIds.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
        </label>

        <button
          type="submit"
          className="mt-5 bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-sidebar-hover disabled:opacity-60"
          disabled={submitting || loading || stockLoading || availableStock === null}
        >
          {submitting ? "Submitting…" : "Record outbound dispersal"}
        </button>
      </form>
    </section>
  );
}
