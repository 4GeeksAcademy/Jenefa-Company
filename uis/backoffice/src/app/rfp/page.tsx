"use client";

import Link from "next/link";
import { ChangeEvent, useCallback, useEffect, useState } from "react";

const colors = { background: "#f4f7f8", foreground: "#1a2b32", surface: "#ffffff", sidebar: "#0f3d3e", sidebarMuted: "#9ebdbd", sidebarHover: "#165153", accent: "#1f7a7a", border: "#d5e0e2", muted: "#5c7278" };
// Use the same-origin Next.js proxy during local development to avoid browser
// CORS failures (especially when the dev server runs on a forwarded port).
const API_BASE = process.env.NODE_ENV === "development"
  ? "/api/backend"
  : (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000");
type Workstream = { department: string; key_aspects: string; contacts: string[]; warnings?: string[] };
type Ticket = { ticket_id: string; status: string; created_at: string; metrics: Record<string, number>; synthesizer_payload?: { sales_summary?: string; workstream_structure?: Workstream[] } | null; error?: string | null };

export default function RfpPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const getRequestHeaders = () => {
    const storedToken = typeof window === "undefined"
      ? ""
      : window.localStorage.getItem("hc_auth_token")?.trim() ?? "";
    return storedToken ? { Authorization: `Bearer ${storedToken}` } : {};
  };

  const refresh = useCallback(async () => {
    if (!getRequestHeaders().Authorization && process.env.NODE_ENV !== "development") { setError("Sign in to view RFP intake tickets."); return; }
    try {
      const response = await fetch(`${API_BASE}/rfp/tickets`, { headers: getRequestHeaders(), cache: "no-store" });
      if (!response.ok) throw new Error(response.status === 401 ? "Your session has expired. Sign in again." : "Unable to load RFP tickets.");
      setTickets(await response.json()); setError("");
    } catch (cause) {
      setError(cause instanceof Error && cause.message !== "Failed to fetch"
        ? cause.message
        : "Could not reach the HealthCore API. Ensure it is running on port 8000, then refresh this page.");
    }
  }, []);

  useEffect(() => { void refresh(); const timer = window.setInterval(() => void refresh(), 5000); return () => window.clearInterval(timer); }, [refresh]);

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!getRequestHeaders().Authorization && process.env.NODE_ENV !== "development") { setError("Sign in to upload an RFP."); return; }
    const body = new FormData(); body.append("file", file); setBusy(true); setError("");
    try {
      const response = await fetch(`${API_BASE}/rfp/tickets`, { method: "POST", headers: getRequestHeaders(), body });
      if (!response.ok) { const payload = await response.json().catch(() => ({})); throw new Error(payload.detail ?? "Upload failed."); }
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error && cause.message !== "Failed to fetch"
        ? cause.message
        : "Could not reach the HealthCore API. Ensure it is running on port 8000, then try the upload again.");
    }
    finally { setBusy(false); event.target.value = ""; }
  }

  return <div style={{ minHeight: "100vh", display: "flex", background: colors.background, color: colors.foreground, fontFamily: "Arial, sans-serif" }}>
    <aside style={{ width: 240, flexShrink: 0, display: "flex", flexDirection: "column", background: colors.sidebar, color: "white" }}><div style={{ padding: "28px 24px", borderBottom: "1px solid rgba(255,255,255,.1)" }}><div style={{ fontFamily: "Georgia, serif", fontSize: 24 }}>HealthCore</div><div style={{ marginTop: 8, color: colors.sidebarMuted, fontSize: 11, textTransform: "uppercase", letterSpacing: ".16em" }}>Internal use only</div></div><nav aria-label="Backoffice navigation" style={{ display: "flex", flex: 1, flexDirection: "column", gap: 5, padding: "20px 12px" }}>{[{ href: "/", label: "Overview" }, { href: "/reporting", label: "Executive reporting" }, { href: "/inventory", label: "Clinic supplies" }, { href: "/rfp", label: "RFP intake" }].map(item => <Link key={item.href} href={item.href} style={{ display: "block", borderRadius: 6, padding: "11px 13px", color: item.href === "/rfp" ? "white" : colors.sidebarMuted, background: item.href === "/rfp" ? colors.sidebarHover : "transparent", textDecoration: "none", fontSize: 14 }}>{item.label}</Link>)}</nav><div style={{ padding: "16px 24px", borderTop: "1px solid rgba(255,255,255,.1)", color: colors.sidebarMuted, fontSize: 11 }}>Staff only · HIPAA / UK GDPR</div></aside>
    <div style={{ minWidth: 0, flex: 1 }}><header style={{ borderBottom: `1px solid ${colors.border}`, background: colors.surface, padding: "20px 36px" }}><div style={{ color: colors.muted, fontSize: 11, fontWeight: 700, letterSpacing: ".14em", textTransform: "uppercase" }}>Operations workspace</div><h1 style={{ margin: "5px 0 0", fontFamily: "Georgia, serif", fontSize: 24, fontWeight: 400 }}>RFP intake & routing</h1></header>
      <main style={{ maxWidth: 1180, margin: "0 auto", padding: "40px 36px" }}><section style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 20, marginBottom: 28 }}><div><p style={{ maxWidth: 680, margin: 0, color: colors.muted, lineHeight: 1.7 }}>Upload a proposal request to extract its requirements, route sections to the responsible teams, and prepare a sales handoff. Processing continues asynchronously.</p></div><label style={{ flexShrink: 0, cursor: busy ? "wait" : "pointer", borderRadius: 5, background: colors.accent, padding: "12px 17px", color: "white", fontSize: 13, fontWeight: 700 }}>{busy ? "Uploading…" : "Upload PDF"}<input aria-label="Upload RFP PDF" type="file" accept="application/pdf,.pdf" disabled={busy} onChange={upload} style={{ display: "none" }} /></label></section>
        {error ? <div role="alert" style={{ marginBottom: 20, border: "1px solid #f0b8b8", borderRadius: 8, background: "#fff5f5", padding: 14, color: "#8b2525" }}>{error}</div> : null}
        <section aria-label="RFP ticket list" style={{ display: "grid", gap: 16 }}>{tickets.length ? tickets.map(ticket => <article key={ticket.ticket_id} style={{ border: `1px solid ${colors.border}`, borderRadius: 8, background: colors.surface, padding: 22 }}><div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: 12 }}><div><strong>Ticket {ticket.ticket_id.slice(0, 8)}</strong><div style={{ marginTop: 5, color: colors.muted, fontSize: 12 }}>Received {new Date(ticket.created_at).toLocaleString()}</div></div><span style={{ borderRadius: 20, background: ticket.status === "intake_complete" ? "#e3f3e9" : ticket.status === "discarded" || ticket.status === "failed" ? "#fff0ee" : "#e9f1f5", padding: "7px 11px", fontSize: 12, fontWeight: 700 }}>{ticket.status.replaceAll("_", " ")}</span></div>
          {ticket.error ? <p role="alert" style={{ color: "#8b2525" }}>{ticket.error}</p> : null}{ticket.metrics?.word_count ? <p style={{ color: colors.muted, fontSize: 13 }}>Readability: grade {ticket.metrics.flesch_kincaid_grade_level} · {ticket.metrics.estimated_tokens} estimated tokens</p> : null}
          {ticket.synthesizer_payload?.sales_summary ? <><h2 style={{ marginBottom: 8, fontFamily: "Georgia, serif", fontWeight: 400 }}>Sales handoff</h2><p style={{ whiteSpace: "pre-wrap", lineHeight: 1.6 }}>{ticket.synthesizer_payload.sales_summary}</p><div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 12 }}>{(ticket.synthesizer_payload.workstream_structure ?? []).map((workstream, index) => <section key={`${ticket.ticket_id}-${workstream.department}-${index}`} style={{ border: `1px solid ${colors.border}`, borderRadius: 6, padding: 15 }}><strong>{workstream.department}</strong><p style={{ whiteSpace: "pre-wrap", color: colors.muted, fontSize: 13, lineHeight: 1.55 }}>{workstream.key_aspects}</p>{workstream.contacts.length ? <div style={{ fontSize: 12 }}>Contacts: {workstream.contacts.join(", ")}</div> : null}{workstream.warnings?.map(warning => <p key={warning} style={{ color: "#8a5a00", fontSize: 12 }}>{warning}</p>)}</section>)}</div></> : null}
        </article>) : <article style={{ border: `1px solid ${colors.border}`, borderRadius: 8, background: colors.surface, padding: 28, color: colors.muted }}>No RFP tickets yet. Upload a PDF to start an intake.</article>}</section>
      </main></div></div>;
}
