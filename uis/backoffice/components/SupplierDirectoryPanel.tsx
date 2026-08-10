"use client";

import { FormEvent, useCallback, useEffect, useState, useTransition } from "react";
import {
  SUPPLIER_CATEGORIES,
  SUPPLIER_COUNTRIES,
  createSupplier,
  currencyForCountry,
  listSuppliers,
  type Supplier,
  type SupplierCountry,
  type SupplierStatus,
  updateSupplierRate,
  updateSupplierStatus,
} from "@/lib/supplierApi";

function formatCategory(value: string): string {
  return value.replaceAll("_", " ");
}

function StatusBadge({ status }: { status: SupplierStatus }) {
  const active = status === "active";
  return (
    <span
      className={`inline-flex rounded-md px-2 py-0.5 text-xs font-semibold ${
        active
          ? "bg-emerald-100 text-emerald-800"
          : "bg-amber-100 text-amber-900"
      }`}
    >
      {status}
    </span>
  );
}

export function SupplierDirectoryPanel() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [countryFilter, setCountryFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [rateDrafts, setRateDrafts] = useState<Record<number, string>>({});
  const [isPending, startTransition] = useTransition();

  const [name, setName] = useState("");
  const [country, setCountry] = useState<SupplierCountry>("USA");
  const [category, setCategory] = useState<string>(SUPPLIER_CATEGORIES[0]);
  const [monthlyRate, setMonthlyRate] = useState("");
  const [status, setStatus] = useState<SupplierStatus>("active");
  const [compliance, setCompliance] = useState("");
  const [contactEmail, setContactEmail] = useState("");

  const refresh = useCallback(() => {
    startTransition(async () => {
      try {
        setError(null);
        const rows = await listSuppliers({
          country: countryFilter || undefined,
          category: categoryFilter || undefined,
        });
        setSuppliers(rows);
        setRateDrafts(
          Object.fromEntries(
            rows.map((row) => [row.id, String(row.monthly_rate)])
          )
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load suppliers.");
      }
    });
  }, [categoryFilter, countryFilter]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  function onCreate(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    const rate = Number(monthlyRate);
    if (!name.trim() || !(rate > 0)) {
      setFormError("Name and a monthly rate greater than zero are required.");
      return;
    }
    startTransition(async () => {
      try {
        await createSupplier({
          name: name.trim(),
          country,
          categories: [category],
          monthly_rate: rate,
          currency: currencyForCountry(country),
          status,
          compliance_agreement: (compliance || null) as Supplier["compliance_agreement"],
          contact_email: contactEmail.trim() || null,
        });
        setName("");
        setMonthlyRate("");
        setCompliance("");
        setContactEmail("");
        setStatus("active");
        refresh();
      } catch (err) {
        setFormError(
          err instanceof Error ? err.message : "Could not create supplier."
        );
      }
    });
  }

  function onSaveRate(id: number) {
    const rate = Number(rateDrafts[id]);
    if (!(rate > 0)) {
      setError("Monthly rate must be greater than zero.");
      return;
    }
    startTransition(async () => {
      try {
        setError(null);
        await updateSupplierRate(id, rate);
        refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Rate update failed.");
      }
    });
  }

  function onToggleStatus(supplier: Supplier) {
    const next: SupplierStatus =
      supplier.status === "active" ? "suspended" : "active";
    startTransition(async () => {
      try {
        setError(null);
        await updateSupplierStatus(supplier.id, next);
        refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Status update failed.");
      }
    });
  }

  return (
    <div className="flex flex-col gap-8">
      <section className="rounded-lg border border-border bg-surface px-6 py-8">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">
          People &amp; compliance
        </p>
        <h2 className="mt-2 font-display text-3xl tracking-tight text-foreground">
          Supplier directory
        </h2>
        <p className="mt-3 max-w-2xl text-base leading-7 text-muted">
          Central registry for clinical and technology vendors. Filter by market,
          track monthly rates, and confirm BAA / DPA coverage for Claire&apos;s
          audits.
        </p>
      </section>

      <section className="flex flex-wrap items-end gap-4 border border-border bg-surface px-4 py-4">
        <div>
          <label
            htmlFor="country-filter"
            className="mb-1 block text-xs font-semibold uppercase tracking-[0.12em] text-muted"
          >
            Country
          </label>
          <select
            id="country-filter"
            className="border border-border bg-background px-3 py-2 text-sm"
            value={countryFilter}
            onChange={(e) => setCountryFilter(e.target.value)}
          >
            <option value="">All</option>
            {SUPPLIER_COUNTRIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label
            htmlFor="category-filter"
            className="mb-1 block text-xs font-semibold uppercase tracking-[0.12em] text-muted"
          >
            Category
          </label>
          <select
            id="category-filter"
            className="border border-border bg-background px-3 py-2 text-sm"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="">All</option>
            {SUPPLIER_CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {formatCategory(c)}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          onClick={refresh}
          className="border border-border bg-background px-3 py-2 text-sm text-foreground hover:bg-accent-soft"
          disabled={isPending}
        >
          {isPending ? "Loading…" : "Refresh"}
        </button>
      </section>

      {error ? (
        <div
          role="alert"
          className="border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900"
        >
          {error}
        </div>
      ) : null}

      <section className="border border-border bg-surface px-4 py-5">
        <h3 className="font-display text-xl text-foreground">Register supplier</h3>
        <form
          onSubmit={onCreate}
          className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-3"
        >
          <div>
            <label className="mb-1 block text-xs text-muted" htmlFor="supplier-name">
              Name
            </label>
            <input
              id="supplier-name"
              className="w-full border border-border px-3 py-2 text-sm"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted" htmlFor="supplier-country">
              Country
            </label>
            <select
              id="supplier-country"
              className="w-full border border-border px-3 py-2 text-sm"
              value={country}
              onChange={(e) => setCountry(e.target.value as SupplierCountry)}
            >
              {SUPPLIER_COUNTRIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted" htmlFor="supplier-category">
              Category
            </label>
            <select
              id="supplier-category"
              className="w-full border border-border px-3 py-2 text-sm"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {SUPPLIER_CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {formatCategory(c)}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted" htmlFor="supplier-rate">
              Monthly rate ({currencyForCountry(country)})
            </label>
            <input
              id="supplier-rate"
              type="number"
              min="0.01"
              step="0.01"
              className="w-full border border-border px-3 py-2 text-sm"
              value={monthlyRate}
              onChange={(e) => setMonthlyRate(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted" htmlFor="supplier-status">
              Status
            </label>
            <select
              id="supplier-status"
              className="w-full border border-border px-3 py-2 text-sm"
              value={status}
              onChange={(e) => setStatus(e.target.value as SupplierStatus)}
            >
              <option value="active">active</option>
              <option value="suspended">suspended</option>
            </select>
          </div>
          <div>
            <label
              className="mb-1 block text-xs text-muted"
              htmlFor="supplier-compliance"
            >
              Compliance agreement
            </label>
            <select
              id="supplier-compliance"
              className="w-full border border-border px-3 py-2 text-sm"
              value={compliance}
              onChange={(e) => setCompliance(e.target.value)}
            >
              <option value="">None</option>
              <option value="BAA">BAA</option>
              <option value="DPA">DPA</option>
              <option value="both">both</option>
            </select>
          </div>
          <div className="md:col-span-2 lg:col-span-3">
            <label className="mb-1 block text-xs text-muted" htmlFor="supplier-email">
              Contact email
            </label>
            <input
              id="supplier-email"
              type="email"
              className="w-full border border-border px-3 py-2 text-sm md:max-w-md"
              value={contactEmail}
              onChange={(e) => setContactEmail(e.target.value)}
            />
          </div>
          {formError ? (
            <p className="md:col-span-2 lg:col-span-3 text-sm text-red-700">
              {formError}
            </p>
          ) : null}
          <div className="md:col-span-2 lg:col-span-3">
            <button
              type="submit"
              disabled={isPending}
              className="bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-sidebar-hover disabled:opacity-60"
            >
              Create supplier
            </button>
          </div>
        </form>
      </section>

      <section className="overflow-x-auto border border-border bg-surface">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-border text-xs uppercase tracking-[0.08em] text-muted">
            <tr>
              <th className="px-4 py-3 font-semibold">Name</th>
              <th className="px-4 py-3 font-semibold">Country</th>
              <th className="px-4 py-3 font-semibold">Categories</th>
              <th className="px-4 py-3 font-semibold">Monthly rate</th>
              <th className="px-4 py-3 font-semibold">Compliance</th>
              <th className="px-4 py-3 font-semibold">Status</th>
              <th className="px-4 py-3 font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody>
            {suppliers.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-muted">
                  No suppliers match the current filters. Seed the API or create
                  one above.
                </td>
              </tr>
            ) : (
              suppliers.map((supplier) => (
                <tr
                  key={supplier.id}
                  className={`border-b border-panel-line ${
                    supplier.status === "suspended" ? "bg-amber-50/40" : ""
                  }`}
                >
                  <td className="px-4 py-3">
                    <p className="font-medium text-foreground">{supplier.name}</p>
                    <p className="text-xs text-muted">
                      updated {supplier.updated_at}
                    </p>
                  </td>
                  <td className="px-4 py-3">{supplier.country}</td>
                  <td className="px-4 py-3">
                    {supplier.categories.map(formatCategory).join(", ")}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <input
                        type="number"
                        min="0.01"
                        step="0.01"
                        className="w-28 border border-border px-2 py-1"
                        value={rateDrafts[supplier.id] ?? ""}
                        onChange={(e) =>
                          setRateDrafts((prev) => ({
                            ...prev,
                            [supplier.id]: e.target.value,
                          }))
                        }
                      />
                      <span className="text-xs text-muted">{supplier.currency}</span>
                      <button
                        type="button"
                        className="bg-accent px-2 py-1 text-xs font-medium text-white hover:bg-sidebar-hover"
                        onClick={() => onSaveRate(supplier.id)}
                        disabled={isPending}
                      >
                        Save
                      </button>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {supplier.compliance_agreement ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={supplier.status} />
                  </td>
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      className="border border-border px-2 py-1 text-xs hover:bg-accent-soft"
                      onClick={() => onToggleStatus(supplier)}
                      disabled={isPending}
                    >
                      {supplier.status === "active" ? "Suspend" : "Activate"}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}
