"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { getAuthToken } from "@/lib/authStorage";
import { toUserFacingMessage } from "@/lib/userFacingError";
import {
  createProduct,
  fetchOrders,
  fetchProducts,
  recordInbound,
  recordOutbound,
  type MedicalSupplyRead,
  type OrderRead,
} from "@/lib/inventoryApi";

const inputClass =
  "mt-1 w-full border border-border bg-background px-3 py-2 text-sm text-foreground";
const labelClass = "block text-xs font-semibold uppercase tracking-[0.12em] text-muted";
const buttonClass =
  "bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sidebar-hover disabled:opacity-60";

export function InventoryPanel() {
  const [signedIn, setSignedIn] = useState(false);
  const [products, setProducts] = useState<MedicalSupplyRead[]>([]);
  const [orders, setOrders] = useState<OrderRead[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    const [catalog, log] = await Promise.all([fetchProducts(), fetchOrders()]);
    setProducts(catalog);
    setOrders(log);
  }, []);

  useEffect(() => {
    const token = getAuthToken();
    setSignedIn(Boolean(token));
    if (!token) return;
    void load().catch((err: unknown) => {
      setError(toUserFacingMessage(err));
    });
  }, [load]);

  if (!signedIn) {
    return (
      <section className="rounded-lg border border-border bg-surface px-6 py-8">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">
          Clinic supply network
        </p>
        <h2 className="mt-2 font-display text-3xl tracking-tight text-foreground">
          Sign in required
        </h2>
        <p className="mt-3 max-w-2xl text-base leading-7 text-muted">
          Inventory ledgers are restricted. Sign in with a clinic operator
          account to view computed stock and post inbound or outbound movements.
        </p>
        <Link
          href="/login"
          className="mt-6 inline-flex bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-sidebar-hover"
        >
          Go to sign in
        </Link>
      </section>
    );
  }

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setBusy(true);
    setError(null);
    setStatus(null);
    try {
      await createProduct({
        name: String(data.get("name") || ""),
        sku: String(data.get("sku") || ""),
        clinic_id: String(data.get("clinic_id") || ""),
        regulatory_tier: String(data.get("regulatory_tier") || ""),
      });
      form.reset();
      setStatus("Supply registered with a starting balance of 0.");
      await load();
    } catch (err: unknown) {
      setError(toUserFacingMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function onLedger(
    event: FormEvent<HTMLFormElement>,
    kind: "inbound" | "outbound"
  ) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setBusy(true);
    setError(null);
    setStatus(null);
    try {
      const payload = {
        medical_supply_id: Number(data.get("medical_supply_id")),
        quantity: Number(data.get("quantity")),
        clinic_id: String(data.get("clinic_id") || ""),
      };
      if (kind === "inbound") {
        await recordInbound(payload);
        setStatus("Inbound shipment recorded.");
      } else {
        await recordOutbound(payload);
        setStatus("Outbound deployment recorded.");
      }
      form.reset();
      await load();
    } catch (err: unknown) {
      setError(toUserFacingMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <section className="rounded-lg border border-border bg-surface px-6 py-8">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">
          Clinic supply network
        </p>
        <h2 className="mt-2 font-display text-3xl tracking-tight text-foreground">
          Medical supply ledger
        </h2>
        <p className="mt-3 max-w-2xl text-base leading-7 text-muted">
          Stock is never stored on catalog rows. Current balances are computed
          from inbound receipts minus outbound deployments, partitioned by
          clinic.
        </p>
      </section>

      {error ? (
        <div role="alert" className="border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900">
          <p className="font-semibold">Inventory request failed</p>
          <p className="mt-1">{error}</p>
        </div>
      ) : null}
      {status ? (
        <div role="status" className="border border-border bg-accent-soft px-4 py-3 text-sm">
          {status}
        </div>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2">
        {products.map((item) => (
          <div key={item.id} className="border border-border bg-surface px-4 py-5">
            <p className="text-xs uppercase tracking-[0.14em] text-muted">{item.sku}</p>
            <p className="mt-2 font-display text-2xl text-foreground">{item.name}</p>
            <p className="mt-1 text-sm text-muted">
              {item.clinic_id} · {item.regulatory_tier}
            </p>
            <p className="mt-4 font-display text-3xl text-foreground">{item.current_stock}</p>
            <p className="text-xs uppercase tracking-[0.14em] text-muted">Computed stock</p>
          </div>
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <form onSubmit={onCreate} className="border border-border bg-surface px-4 py-5">
          <h3 className="text-sm font-semibold text-foreground">Register supply</h3>
          <label className={`${labelClass} mt-4`}>
            Name
            <input className={inputClass} name="name" required />
          </label>
          <label className={`${labelClass} mt-3`}>
            SKU
            <input className={inputClass} name="sku" required />
          </label>
          <label className={`${labelClass} mt-3`}>
            Clinic ID
            <input className={inputClass} name="clinic_id" required placeholder="CLINIC-TX-01" />
          </label>
          <label className={`${labelClass} mt-3`}>
            Regulatory tier
            <input className={inputClass} name="regulatory_tier" required />
          </label>
          <button type="submit" className={`${buttonClass} mt-4`} disabled={busy}>
            Create at stock 0
          </button>
        </form>

        <form
          onSubmit={(event) => void onLedger(event, "inbound")}
          className="border border-border bg-surface px-4 py-5"
        >
          <h3 className="text-sm font-semibold text-foreground">Inbound receipt</h3>
          <label className={`${labelClass} mt-4`}>
            Supply ID
            <input className={inputClass} name="medical_supply_id" type="number" required min={1} />
          </label>
          <label className={`${labelClass} mt-3`}>
            Quantity
            <input className={inputClass} name="quantity" type="number" required min={1} />
          </label>
          <label className={`${labelClass} mt-3`}>
            Clinic ID
            <input className={inputClass} name="clinic_id" required />
          </label>
          <button type="submit" className={`${buttonClass} mt-4`} disabled={busy}>
            Log inbound
          </button>
        </form>

        <form
          onSubmit={(event) => void onLedger(event, "outbound")}
          className="border border-border bg-surface px-4 py-5"
        >
          <h3 className="text-sm font-semibold text-foreground">Outbound deployment</h3>
          <label className={`${labelClass} mt-4`}>
            Supply ID
            <input className={inputClass} name="medical_supply_id" type="number" required min={1} />
          </label>
          <label className={`${labelClass} mt-3`}>
            Quantity
            <input className={inputClass} name="quantity" type="number" required min={1} />
          </label>
          <label className={`${labelClass} mt-3`}>
            Clinic ID
            <input className={inputClass} name="clinic_id" required />
          </label>
          <button type="submit" className={`${buttonClass} mt-4`} disabled={busy}>
            Log outbound
          </button>
        </form>
      </section>

      <section className="border border-border bg-surface px-4 py-5">
        <h3 className="text-sm font-semibold text-foreground">Unified order log</h3>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-panel-line text-xs uppercase tracking-[0.12em] text-muted">
                <th className="py-2 pr-3">Kind</th>
                <th className="py-2 pr-3">SKU</th>
                <th className="py-2 pr-3">Qty</th>
                <th className="py-2 pr-3">Clinic</th>
                <th className="py-2 pr-3">Operator</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-panel-line">
              {orders.map((row) => (
                <tr key={`${row.kind}-${row.id}`}>
                  <td className="py-2 pr-3 capitalize">{row.kind}</td>
                  <td className="py-2 pr-3">{row.medical_supply.sku}</td>
                  <td className="py-2 pr-3">{row.quantity}</td>
                  <td className="py-2 pr-3">{row.clinic_id}</td>
                  <td className="py-2 pr-3 font-mono text-xs">{row.user_uuid}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
