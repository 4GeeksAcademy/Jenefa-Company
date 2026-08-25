"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/backoffice/inventory/products", label: "Products ledger" },
  { href: "/backoffice/inventory/orders/inbound", label: "Inbound intake" },
  { href: "/backoffice/inventory/orders/outbound", label: "Outbound dispersal" },
  { href: "/backoffice/inventory/orders", label: "Orders history" },
] as const;

export function InventorySubnav() {
  const pathname = usePathname();

  return (
    <nav aria-label="Inventory navigation" className="flex flex-wrap gap-2">
      {navItems.map((item) => {
        const active = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={`rounded-md border px-3 py-2 text-sm transition-colors ${
              active
                ? "border-accent bg-accent text-white"
                : "border-border bg-surface text-foreground hover:border-accent"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
