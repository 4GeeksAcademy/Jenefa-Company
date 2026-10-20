"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getAuthDisplayName } from "@/lib/authStorage";
import { logoutAndRedirect } from "@/lib/authStorage";
import { initTelemetry, track } from "@/lib/telemetry";

const navGroups = [
  { label: "Knowledge base", items: [{ href: "/", label: "Overview", icon: "◉" }] },
  {
    label: "Business logic",
    items: [
      { href: "/reporting", label: "Business Reporting", icon: "▥" },
      { href: "/incidents", label: "Incidents Analysis", icon: "✚" },
      { href: "/talent", label: "Candidate Sourcing", icon: "◆" },
    ],
  },
  {
    label: "Technical data",
    items: [
      { href: "/inventory", label: "Inventory Ledger", icon: "▣" },
      { href: "/rfp", label: "RFP Intake", icon: "✉" },
    ],
  },
  { label: "Operating assistant", items: [{ href: "/assistant", label: "Live Support Chat", icon: "◇" }] },
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
    /* FIXED: Changed to h-screen w-screen overflow-hidden to lock the outer viewport completely */
    <div className="h-screen w-screen overflow-hidden bg-[linear-gradient(135deg,#e5e7eb_0%,#f8fafc_48%,#f1f5f9_100%)] p-4 lg:p-6">
      <div className="flex h-full w-full min-h-0 overflow-hidden bg-background shadow-[0_18px_60px_rgba(23,37,84,0.14)]">
        
        {/* SIDEBAR: Kept flex-col h-full to remain completely locked on the left side */}
        <aside className="flex h-full w-60 shrink-0 flex-col bg-sidebar text-white">
          <div className="border-b border-white/10 px-6 py-4">
  <div className="flex items-center gap-3">
    {/* CHANGE: Reduced size from h-10 w-10 to h-8 w-8, and text-base to text-sm */}
    <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center bg-accent text-sm font-bold text-white">
      HC
    </span>
    {/* CHANGE: Reduced text size from text-lg to text-base */}
    <p className="font-display text-base tracking-tight">HealthCore</p>
  </div>
</div>
          <nav className="flex flex-1 flex-col overflow-y-auto px-3 py-4" aria-label="Web app">
            {navGroups.map((group) => (
              <div key={group.label} className="mb-5 flex flex-col gap-2">
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
                      className={`block px-3 py-2 text-sm transition-colors ${
                        active
                          ? "bg-sidebar-hover font-medium text-white active:bg-[#0284c7]"
                          : "text-sidebar-muted hover:bg-sidebar-hover hover:text-white active:bg-[#0284c7]"
                      }`}
                    >
                      <span aria-hidden="true" className="mr-2 inline-block w-4 text-center text-sm text-sidebar-muted">
                        {item.icon}
                      </span>
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

        {/* RIGHT CONTENT CONTAINER */}
        <div className="flex h-full min-h-0 min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-10 flex shrink-0 items-start justify-between border-b border-border bg-surface px-6 py-4 leading-6">
            <div>
              <p className="text-2xl font-bold uppercase tracking-widest text-muted">
                Backoffice
              </p>
              <h1 className="font-display text-xs font-semibold text-foreground">Internal Use Only</h1>
            </div>
            <div className="flex flex-col items-end">
              {displayName ? (
                <p className="text-sm font-medium text-foreground">
                  Welcome, <span className="text-accent">{displayName}</span>
                </p>
              ) : null}

              <button
                type="button"
                onClick={() => logoutAndRedirect()}
                className="text-sm text-muted hover:text-foreground"
              >
                Log out
              </button>
            </div>
          </header>
          
          {/* MAIN CONTENT AREA: This is the ONLY element that receives the scrollbar */}
          <main className="min-h-0 flex-1 overflow-y-auto px-6 py-8">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
