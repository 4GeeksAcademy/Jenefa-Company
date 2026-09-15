import Link from "next/link";

const colors = {
  background: "#f4f7f8",
  foreground: "#1a2b32",
  surface: "#ffffff",
  sidebar: "#0f3d3e",
  sidebarMuted: "#9ebdbd",
  sidebarHover: "#165153",
  accent: "#1f7a7a",
  accentSoft: "#d7ecec",
  border: "#d5e0e2",
  muted: "#5c7278",
};

const navItems = [
  { href: "/", label: "Overview", active: true },
  { href: "/", label: "Executive reporting" },
  { href: "/inventory", label: "Clinic supplies" },
];

const metrics = [
  { label: "Network clinics", value: "12", note: "Across US and UK" },
  { label: "Open operational alerts", value: "04", note: "Requires review" },
  { label: "Inventory status", value: "Stable", note: "Last checked today" },
];

export default function BackofficeHomePage() {
  return (
    <div style={{ minHeight: "100vh", display: "flex", background: colors.background, color: colors.foreground, fontFamily: "Arial, sans-serif" }}>
      <aside style={{ width: 240, flexShrink: 0, display: "flex", flexDirection: "column", background: colors.sidebar, color: "white" }}>
        <div style={{ padding: "28px 24px", borderBottom: "1px solid rgba(255,255,255,.1)" }}>
          <div style={{ fontFamily: "Georgia, serif", fontSize: 24 }}>HealthCore</div>
          <div style={{ marginTop: 8, color: colors.sidebarMuted, fontSize: 11, textTransform: "uppercase", letterSpacing: ".16em" }}>Internal use only</div>
        </div>
        <nav aria-label="Backoffice navigation" style={{ display: "flex", flex: 1, flexDirection: "column", gap: 5, padding: "20px 12px" }}>
          {navItems.map((item) => (
            <Link key={item.href} href={item.href} style={{ display: "block", borderRadius: 6, padding: "11px 13px", color: item.active ? "white" : colors.sidebarMuted, background: item.active ? colors.sidebarHover : "transparent", textDecoration: "none", fontSize: 14, fontWeight: item.active ? 600 : 400 }}>
              {item.label}
            </Link>
          ))}
        </nav>
        <div style={{ padding: "16px 24px", borderTop: "1px solid rgba(255,255,255,.1)", color: colors.sidebarMuted, fontSize: 11 }}>Staff only · HIPAA / UK GDPR</div>
      </aside>

      <div style={{ minWidth: 0, flex: 1 }}>
        <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 24, borderBottom: `1px solid ${colors.border}`, background: colors.surface, padding: "20px 36px" }}>
          <div>
            <div style={{ color: colors.muted, fontSize: 11, fontWeight: 700, letterSpacing: ".14em", textTransform: "uppercase" }}>Operations workspace</div>
            <div style={{ marginTop: 5, fontFamily: "Georgia, serif", fontSize: 22 }}>Backoffice</div>
          </div>
          <div style={{ textAlign: "right", fontSize: 13 }}>
            <div style={{ fontWeight: 600 }}>Welcome, James Osei</div>
            <div style={{ marginTop: 4, color: colors.muted }}>Austin tech unit</div>
          </div>
        </header>

        <main style={{ maxWidth: 1180, margin: "0 auto", padding: "40px 36px" }}>
          <section style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 24, marginBottom: 32 }}>
            <div>
              <div style={{ color: colors.accent, fontSize: 12, fontWeight: 700, letterSpacing: ".16em", textTransform: "uppercase" }}>Good morning, James</div>
              <h1 style={{ margin: "10px 0 8px", fontFamily: "Georgia, serif", fontSize: "clamp(32px, 5vw, 48px)", fontWeight: 400, letterSpacing: "-.03em" }}>A clearer view of care operations.</h1>
              <p style={{ maxWidth: 620, margin: 0, color: colors.muted, fontSize: 15, lineHeight: 1.7 }}>Monitor clinic activity, review executive performance, and keep essential supplies moving across the network.</p>
            </div>
            <Link href="/" style={{ flexShrink: 0, borderRadius: 5, background: colors.accent, padding: "12px 17px", color: "white", textDecoration: "none", fontSize: 13, fontWeight: 700 }}>View reporting</Link>
          </section>

          <section aria-label="Operational summary" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: 16, marginBottom: 28 }}>
            {metrics.map((metric) => (
              <article key={metric.label} style={{ border: `1px solid ${colors.border}`, borderRadius: 8, background: colors.surface, padding: "22px 20px" }}>
                <div style={{ color: colors.muted, fontSize: 11, fontWeight: 700, letterSpacing: ".12em", textTransform: "uppercase" }}>{metric.label}</div>
                <div style={{ marginTop: 13, fontFamily: "Georgia, serif", fontSize: 30 }}>{metric.value}</div>
                <div style={{ marginTop: 6, color: colors.muted, fontSize: 12 }}>{metric.note}</div>
              </article>
            ))}
          </section>

          <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 18 }}>
            <article style={{ border: `1px solid ${colors.border}`, borderRadius: 8, background: colors.surface, padding: 24 }}>
              <div style={{ color: colors.accent, fontSize: 11, fontWeight: 700, letterSpacing: ".15em", textTransform: "uppercase" }}>Executive reporting</div>
              <h2 style={{ margin: "12px 0 8px", fontFamily: "Georgia, serif", fontSize: 25, fontWeight: 400 }}>Weekly network performance</h2>
              <p style={{ margin: "0 0 20px", color: colors.muted, fontSize: 14, lineHeight: 1.65 }}>Review appointment volume, no-show rates, claims denials, and settled revenue by clinic.</p>
              <Link href="/" style={{ color: colors.accent, fontSize: 13, fontWeight: 700, textDecoration: "none" }}>Open reporting →</Link>
            </article>
            <article style={{ border: `1px solid ${colors.border}`, borderRadius: 8, background: colors.surface, padding: 24 }}>
              <div style={{ color: colors.accent, fontSize: 11, fontWeight: 700, letterSpacing: ".15em", textTransform: "uppercase" }}>Inventory control</div>
              <h2 style={{ margin: "12px 0 8px", fontFamily: "Georgia, serif", fontSize: 25, fontWeight: 400 }}>Clinic supplies ledger</h2>
              <p style={{ margin: "0 0 20px", color: colors.muted, fontSize: 14, lineHeight: 1.65 }}>Check current balances and record inbound deliveries or outbound dispersals.</p>
              <Link href="/inventory" style={{ color: colors.accent, fontSize: 13, fontWeight: 700, textDecoration: "none" }}>Open inventory →</Link>
            </article>
            <article style={{ border: `1px solid ${colors.border}`, borderRadius: 8, background: colors.accentSoft, padding: 24 }}>
              <div style={{ color: colors.sidebar, fontSize: 11, fontWeight: 700, letterSpacing: ".15em", textTransform: "uppercase" }}>Operations note</div>
              <h2 style={{ margin: "12px 0 8px", fontFamily: "Georgia, serif", fontSize: 25, fontWeight: 400 }}>Everything in one workspace.</h2>
              <p style={{ margin: 0, color: colors.sidebar, fontSize: 14, lineHeight: 1.65 }}>Use the navigation to move between daily supply work and leadership-level reporting.</p>
            </article>
          </section>
        </main>
      </div>
    </div>
  );
}
