"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getAuthDisplayName } from "@/lib/authStorage";
import { logoutAndRedirect } from "@/lib/authStorage";
import { initTelemetry, track } from "@/lib/telemetry";

const navGroups = [
  { label: "Knowledge base", items: [{ href: "/", label: "Overview" }] },
  {
    label: "Business logic",
    items: [
      { href: "/reporting", label: "Business Reporting" },
      { href: "/incidents", label: "Incidents Analysis" },
      { href: "/talent", label: "Candidate Sourcing" },
    ],
  },
  {
    label: "Technical data",
    items: [
      { href: "/inventory", label: "Inventory Ledger" },
      { href: "/rfp", label: "RFP Intake" },
    ],
  },
  { label: "Agent systems", items: [{ href: "/assistant", label: "Live Support Chat" }] },
] as const;

export function WebShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [displayName, setDisplayName] = useState<string | null>(null);

  // Sync state on path changes via an event queue frame to prevent cascading renders
  useEffect(() => {
    let active = true;
    queueMicrotask(() => {
      if (active) {
        setDisplayName(getAuthDisplayName());
      }
    });
    return () => {
      active = false;
    };
  }, [pathname]);

  useEffect(() => {
    initTelemetry();
  }, []);

  return (
    <div className="flex min-h-full flex-1 bg-background">
      <aside className="flex w-60 shrink-0 flex-col bg-sidebar text-white">
        <div className="border-b border-white/10 px-5 py-6">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent font-bold text-white">
              HC
            </span>
            <p className="font-display text-lg tracking-tight">HealthCore</p>
          </div>
          <p className="mt-2 pl-[52px] text-xs uppercase tracking-[0.16em] text-sidebar-muted">
            Internal use only
          </p>
        </div>
        <nav className="flex flex-1 flex-col px-3 py-4" aria-label="Web app">
          {navGroups.map((group) => (
            <div key={group.label} className="mb-5 flex flex-col gap-1">
              <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-sidebar-muted/70">
                {group.label}
              </p>
              {group.items.map((item) => {
                const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.label}
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    onClick={() =>
                      track("client_navigation_tracked", {
                        origin_route: pathname,
                        destination_route: item.href,
                        user_type: "operations_staff",
                      })
                    }
                    className={`block rounded-full px-3 py-2 text-sm transition-colors ${
                      active
                        ? "bg-sidebar-hover font-medium text-white active:bg-[#0284c7]"
                        : "text-sidebar-muted hover:bg-sidebar-hover hover:text-white active:bg-[#0284c7]"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>
        <div className="border-t border-white/10 px-5 py-4 text-xs text-sidebar-muted">
          Staff only · HIPAA / UK GDPR
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-start justify-between border-b border-border bg-surface px-6 py-4 leading-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">
              Operations workspace
            </p>
            <h1 className="font-display text-xl text-foreground">Backoffice</h1>
          </div>
          <div className="flex flex-col items-end">
            {displayName ? (
              <p className="text-sm font-medium text-foreground">Welcome, {displayName}</p>
            ) : null}
            <p className="text-sm text-muted">Austin tech unit --- James Osei</p>
            <button
              type="button"
              onClick={() => logoutAndRedirect()}
              className="text-sm text-muted hover:text-foreground"
            >
              Log out
            </button>
          </div>
        </header>
        <main className="flex-1 px-6 py-8">{children}</main>
      </div>
    </div>
  );
}
