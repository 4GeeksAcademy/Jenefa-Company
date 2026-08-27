"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchProducts, type MedicalSupplyRead } from "@/lib/inventory";
import { toUserFacingMessage } from "@/lib/userFacingError";
import { useRequireAuth } from "@/lib/useRequireAuth";
import { InventorySubnav } from "@/components/inventory/InventorySubnav";

const LOW_STOCK_THRESHOLD = 20;

export function InventoryProductsView() {
  const { isAuthorized } = useRequireAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [products, setProducts] = useState<MedicalSupplyRead[]>([]);

  useEffect(() => {
    if (!isAuthorized) {
      return;
    }

    void fetchProducts()
      .then((rows) => setProducts(rows))
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
        <h2 className="font-display text-3xl tracking-tight text-foreground">
          Products Inventory Ledger
        </h2>
        <p className="text-sm leading-7 text-muted">
          Live balances are derived from inbound and outbound movement records.
        </p>
        <InventorySubnav />
      </header>

      {error ? (
        <div role="alert" className="border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900">
          <p className="font-semibold">Inventory request failed</p>
          <p className="mt-1">{error}</p>
        </div>
      ) : null}

      <div className="overflow-x-auto rounded-lg border border-border bg-surface">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-panel-line text-xs uppercase tracking-[0.12em] text-muted">
              <th className="px-4 py-3">Clinical Item Name</th>
              <th className="px-4 py-3">Stock Keeping Unit (SKU)</th>
              <th className="px-4 py-3">Available Inventory</th>
              <th className="px-4 py-3">Stock Status</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-panel-line">
            {loading ? (
              <tr>
                <td className="px-4 py-4 text-muted" colSpan={5}>
                  Loading products…
                </td>
              </tr>
            ) : products.length === 0 ? (
              <tr>
                <td className="px-4 py-4 text-muted" colSpan={5}>
                  No products found.
                </td>
              </tr>
            ) : (
              products.map((item) => {
                // Thresholds from product context: >= 20 is stable, < 20 is low stock warning.
                const stable = item.current_stock >= LOW_STOCK_THRESHOLD;
                return (
                  <tr key={item.id}>
                    <td className="px-4 py-4">
                      <p className="font-semibold text-foreground">{item.name}</p>
                      <p className="text-xs text-muted">{item.clinic_id}</p>
                    </td>
                    <td className="px-4 py-4 text-muted">{item.sku}</td>
                    <td className="px-4 py-4 font-semibold text-foreground">{item.current_stock}</td>
                    <td className="px-4 py-4">
                      <span
                        className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                          stable
                            ? "bg-green-100 text-green-900"
                            : "bg-amber-200 text-amber-950"
                        }`}
                      >
                        {stable ? "Stock Level Stable" : "Low Stock Warning"}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex flex-wrap gap-2 text-xs">
                        <Link
                          href={`/backoffice/inventory/orders/inbound?item=${item.id}`}
                          className="rounded border border-border px-2 py-1 hover:border-accent"
                        >
                          Log inbound
                        </Link>
                        <Link
                          href={`/backoffice/inventory/orders/outbound?item=${item.id}`}
                          className="rounded border border-border px-2 py-1 hover:border-accent"
                        >
                          Log outbound
                        </Link>
                      </div>
                    </td>
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
