"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Overview" },
  { href: "/incidents", label: "Incident analysis" },
] as const;

export function WebShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-full flex-1 bg-background">
      <aside className="flex w-60 shrink-0 flex-col bg-sidebar text-white">
        <div className="border-b border-white/10 px-5 py-6">
          <p className="font-display text-lg tracking-tight">HealthCore</p>
          <p className="mt-1 text-xs uppercase tracking-[0.16em] text-sidebar-muted">
            Internal use only
          </p>
        </div>
        <nav className="flex flex-1 flex-col gap-1 px-3 py-4" aria-label="Web app">
          {navItems.map((item) => {
            const active =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.label}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`rounded-md px-3 py-2 text-sm transition-colors ${
                  active
                    ? "bg-sidebar-hover font-medium text-white"
                    : "text-sidebar-muted hover:bg-sidebar-hover hover:text-white"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-white/10 px-5 py-4 text-xs text-sidebar-muted">
          Staff only · HIPAA / UK GDPR
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-border bg-surface px-6 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">
              Operations workspace
            </p>
            <h1 className="font-display text-xl text-foreground">Home</h1>
          </div>
          <p className="text-sm text-muted">Austin tech unit --- James Osei</p>
        </header>
        <main className="flex-1 px-6 py-8">{children}</main>
      </div>
    </div>
  );
}
