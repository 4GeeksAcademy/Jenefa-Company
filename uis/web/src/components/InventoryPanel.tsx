import Link from "next/link";

export function InventoryPanel() {
  return (
    <section className="rounded-lg border border-border bg-surface px-6 py-8">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">
        Clinic supply network
      </p>
      <h2 className="mt-2 font-display text-3xl tracking-tight text-foreground">
        Inventory module moved
      </h2>
      <p className="mt-3 max-w-2xl text-base leading-7 text-muted">
        Inventory tools now run from the dedicated backoffice paths for products,
        inbound intake, outbound dispersal, and audit history.
      </p>
      <Link
        href="/backoffice/inventory/products"
        className="mt-6 inline-flex bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-sidebar-hover"
      >
        Open inventory module
      </Link>
    </section>
  );
}
