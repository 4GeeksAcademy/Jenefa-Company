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
type EvaluationResult = { overall_pass: boolean; feedback_for_generator: string; readability: { pass: boolean; score: number; details: string }; relevance: { pass: boolean; missing_aspects: string[] }; compliance: { pass: boolean; rule_ids: string[]; violations: string[] } };
type ResponseSection = { section_id: string; department_id: string; department: string; draft: string; iteration_count: number; evaluation_result: EvaluationResult };
type ApprovalBranch = { branch_id: string; department_id: string; department: string; owner: string; status: string; decision?: string | null; feedback?: string | null; thread_id: string; iteration_count: number; draft: string; requirements: string; warnings: string[]; changelog: Array<{ iteration: number; draft: string; decision?: string; feedback?: string }> };
type Ticket = { ticket_id: string; status: string; created_at: string; metrics: Record<string, number>; synthesizer_payload?: { sales_summary?: string; workstream_structure?: Workstream[] } | null; response_sections?: ResponseSection[]; approval?: { branches: ApprovalBranch[]; final_proposal: Record<string, unknown> | null } | null; error?: string | null };

export default function RfpPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [generatingTicket, setGeneratingTicket] = useState("");
  const [approvalBusy, setApprovalBusy] = useState("");
  const [approvalFeedback, setApprovalFeedback] = useState<Record<string, string>>({});
  const getRequestHeaders = (): Record<string, string> => {
    // The local API's loopback bypass is intentionally anonymous. Do not send
    // a stale saved session token in development, since it would be validated
    // instead of using that bypass.
    if (process.env.NODE_ENV === "development") return {};
    const storedToken = typeof window === "undefined"
      ? ""
      : window.localStorage.getItem("hc_auth_token")?.trim() ?? "";
    const headers: Record<string, string> = {};
    if (storedToken) headers.Authorization = `Bearer ${storedToken}`;
    return headers;
  };

  const refresh = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/rfp/tickets`, { headers: getRequestHeaders(), cache: "no-store" });
      // A polling 401 should not leave a persistent red authentication banner
      // on this local development page. Keep the last successfully loaded list
      // and let the next poll retry; uploads still report their own failures.
      if (response.status === 401) {
        setError("");
        return;
      }
      if (!response.ok) throw new Error("Unable to load RFP tickets.");
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
    const body = new FormData(); body.append("file", file); setBusy(true); setError("");
    try {
      const response = await fetch(`${API_BASE}/rfp/tickets`, { method: "POST", headers: getRequestHeaders(), body });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        const message = response.status === 401
          ? "Upload was not authorized."
          : payload.detail ?? "Upload failed.";
        throw new Error(message);
      }
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error && cause.message !== "Failed to fetch"
        ? cause.message
        : "Could not reach the HealthCore API. Ensure it is running on port 8000, then try the upload again.");
    }
    finally { setBusy(false); event.target.value = ""; }
  }

  async function generateResponse(ticketId: string) {
    setGeneratingTicket(ticketId); setError("");
    try {
      const response = await fetch(`${API_BASE}/rfp/tickets/${ticketId}/generate-response`, {
        method: "POST",
        headers: getRequestHeaders(),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? "Response generation could not be started.");
      }
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error && cause.message !== "Failed to fetch"
        ? cause.message
        : "Could not reach the HealthCore API. Ensure it is running, then try again.");
    } finally {
      setGeneratingTicket("");
    }
  }

  async function beginApproval(ticketId: string) {
    setApprovalBusy(`${ticketId}:begin`); setError("");
    try {
      const response = await fetch(`${API_BASE}/rfp/tickets/${ticketId}/begin-approval`, { method: "POST", headers: getRequestHeaders() });
      if (!response.ok) { const payload = await response.json().catch(() => ({})); throw new Error(payload.detail ?? "Could not start approvals."); }
      await refresh();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not start approvals."); }
    finally { setApprovalBusy(""); }
  }

  async function decideApproval(ticketId: string, branch: ApprovalBranch, decision: "approve" | "reject" | "request_changes") {
    setApprovalBusy(branch.branch_id); setError("");
    try {
      const response = await fetch(`${API_BASE}/rfp/tickets/${ticketId}/approvals/${encodeURIComponent(branch.department)}/decision`, {
        method: "POST", headers: { ...getRequestHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ decision, feedback: approvalFeedback[branch.branch_id] ?? "" }),
      });
      if (!response.ok) { const payload = await response.json().catch(() => ({})); throw new Error(payload.detail ?? "Approval decision could not be saved."); }
      await refresh();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Approval decision could not be saved."); }
    finally { setApprovalBusy(""); }
  }

  return <div style={{ minHeight: "100vh", display: "flex", background: colors.background, color: colors.foreground, fontFamily: "Arial, sans-serif" }}>
    <aside style={{ width: 240, flexShrink: 0, display: "flex", flexDirection: "column", background: colors.sidebar, color: "white" }}><div style={{ padding: "28px 24px", borderBottom: "1px solid rgba(255,255,255,.1)" }}><div style={{ fontFamily: "Georgia, serif", fontSize: 24 }}>HealthCore</div><div style={{ marginTop: 8, color: colors.sidebarMuted, fontSize: 11, textTransform: "uppercase", letterSpacing: ".16em" }}>Internal use only</div></div><nav aria-label="Backoffice navigation" style={{ display: "flex", flex: 1, flexDirection: "column", gap: 5, padding: "20px 12px" }}>{[{ href: "/", label: "Overview" }, { href: "/reporting", label: "Executive reporting" }, { href: "/inventory", label: "Clinic supplies" }, { href: "/rfp", label: "RFP intake" }].map(item => <Link key={item.href} href={item.href} style={{ display: "block", borderRadius: 6, padding: "11px 13px", color: item.href === "/rfp" ? "white" : colors.sidebarMuted, background: item.href === "/rfp" ? colors.sidebarHover : "transparent", textDecoration: "none", fontSize: 14 }}>{item.label}</Link>)}</nav><div style={{ padding: "16px 24px", borderTop: "1px solid rgba(255,255,255,.1)", color: colors.sidebarMuted, fontSize: 11 }}>Staff only · HIPAA / UK GDPR</div></aside>
    <div style={{ minWidth: 0, flex: 1 }}><header style={{ borderBottom: `1px solid ${colors.border}`, background: colors.surface, padding: "20px 36px" }}><div style={{ color: colors.muted, fontSize: 11, fontWeight: 700, letterSpacing: ".14em", textTransform: "uppercase" }}>Operations workspace</div><h1 style={{ margin: "5px 0 0", fontFamily: "Georgia, serif", fontSize: 24, fontWeight: 400 }}>RFP intake & routing</h1></header>
      <main style={{ maxWidth: 1180, margin: "0 auto", padding: "40px 36px" }}><section style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 20, marginBottom: 28 }}><div><p style={{ maxWidth: 680, margin: 0, color: colors.muted, lineHeight: 1.7 }}>Upload a proposal request to extract its requirements, route sections to the responsible teams, and prepare a sales handoff. Processing continues asynchronously.</p></div><label style={{ flexShrink: 0, cursor: busy ? "wait" : "pointer", borderRadius: 5, background: colors.accent, padding: "12px 17px", color: "white", fontSize: 13, fontWeight: 700 }}>{busy ? "Uploading…" : "Upload PDF"}<input aria-label="Upload RFP PDF" type="file" accept="application/pdf,.pdf" disabled={busy} onChange={upload} style={{ display: "none" }} /></label></section>
        {error ? <div role="alert" style={{ marginBottom: 20, border: "1px solid #f0b8b8", borderRadius: 8, background: "#fff5f5", padding: 14, color: "#8b2525" }}>{error}</div> : null}
        <section aria-label="RFP ticket list" style={{ display: "grid", gap: 16 }}>{tickets.length ? tickets.map(ticket => <article key={ticket.ticket_id} style={{ border: `1px solid ${colors.border}`, borderRadius: 8, background: colors.surface, padding: 22 }}><div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: 12 }}><div><strong>Ticket {ticket.ticket_id.slice(0, 8)}</strong><div style={{ marginTop: 5, color: colors.muted, fontSize: 12 }}>Received {new Date(ticket.created_at).toLocaleString()}</div></div><span style={{ borderRadius: 20, background: ticket.status === "intake_complete" ? "#e3f3e9" : ticket.status === "discarded" || ticket.status === "failed" ? "#fff0ee" : "#e9f1f5", padding: "7px 11px", fontSize: 12, fontWeight: 700 }}>{ticket.status.replaceAll("_", " ")}</span></div>
          {ticket.status === "intake_complete" ? <button type="button" onClick={() => void generateResponse(ticket.ticket_id)} disabled={generatingTicket === ticket.ticket_id} style={{ marginTop: 16, border: 0, borderRadius: 5, background: colors.accent, padding: "10px 14px", color: "white", cursor: generatingTicket === ticket.ticket_id ? "wait" : "pointer", fontWeight: 700 }}>{generatingTicket === ticket.ticket_id ? "Generating drafts…" : "Generate response drafts"}</button> : null}
          {ticket.response_sections?.length && !ticket.approval?.branches?.length && ["under_evaluation", "needs_human_review"].includes(ticket.status) ? <button type="button" onClick={() => void beginApproval(ticket.ticket_id)} disabled={approvalBusy === `${ticket.ticket_id}:begin`} style={{ marginTop: 16, marginLeft: 10, border: 0, borderRadius: 5, background: colors.accent, padding: "10px 14px", color: "white", fontWeight: 700 }}>{approvalBusy === `${ticket.ticket_id}:begin` ? "Preparing approvals…" : "Start departmental approvals"}</button> : null}
          {ticket.error ? <p role="alert" style={{ color: "#8b2525" }}>{ticket.error}</p> : null}{ticket.metrics?.word_count ? <p style={{ color: colors.muted, fontSize: 13 }}>Readability: grade {ticket.metrics.flesch_kincaid_grade_level} · {ticket.metrics.estimated_tokens} estimated tokens</p> : null}
          {ticket.synthesizer_payload?.sales_summary ? <><h2 style={{ marginBottom: 8, fontFamily: "Georgia, serif", fontWeight: 400 }}>Sales handoff</h2><p style={{ whiteSpace: "pre-wrap", lineHeight: 1.6 }}>{ticket.synthesizer_payload.sales_summary}</p><div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 12 }}>{(ticket.synthesizer_payload.workstream_structure ?? []).map((workstream, index) => <section key={`${ticket.ticket_id}-${workstream.department}-${index}`} style={{ border: `1px solid ${colors.border}`, borderRadius: 6, padding: 15 }}><strong>{workstream.department}</strong><p style={{ whiteSpace: "pre-wrap", color: colors.muted, fontSize: 13, lineHeight: 1.55 }}>{workstream.key_aspects}</p>{workstream.contacts.length ? <div style={{ fontSize: 12 }}>Contacts: {workstream.contacts.join(", ")}</div> : null}{workstream.warnings?.map(warning => <p key={warning} style={{ color: "#8a5a00", fontSize: 12 }}>{warning}</p>)}</section>)}</div></> : null}
          {ticket.response_sections?.length ? <><h2 style={{ margin: "26px 0 12px", fontFamily: "Georgia, serif", fontWeight: 400 }}>Response drafts · human review required</h2><div style={{ display: "grid", gap: 12 }}>{ticket.response_sections.map(section => <section key={section.section_id} style={{ border: `1px solid ${section.evaluation_result.overall_pass ? colors.border : "#e2b36f"}`, borderRadius: 6, padding: 16, background: section.evaluation_result.overall_pass ? "#fff" : "#fffaf0" }}><strong>{section.department}</strong><span style={{ marginLeft: 10, fontSize: 12, fontWeight: 700, color: section.evaluation_result.overall_pass ? "#216e43" : "#8a5a00" }}>{section.evaluation_result.overall_pass ? "Evaluator checks passed · human approval still required" : "Provisional · needs human review"}</span><p style={{ color: colors.muted, fontSize: 12 }}>Iterations: {section.iteration_count} · Readability score: {section.evaluation_result.readability.score}</p><pre style={{ whiteSpace: "pre-wrap", font: "inherit", lineHeight: 1.6 }}>{section.draft}</pre>{section.evaluation_result.compliance.violations.map((violation, index) => <p key={`${section.section_id}-violation-${index}`} role="alert" style={{ color: "#8b2525", fontSize: 13 }}>{violation}{section.evaluation_result.compliance.rule_ids[index] ? ` (${section.evaluation_result.compliance.rule_ids[index]})` : ""}</p>)}{section.evaluation_result.feedback_for_generator ? <p style={{ color: "#8a5a00", fontSize: 13 }}>Review notes: {section.evaluation_result.feedback_for_generator}</p> : null}</section>)}</div></> : null}
          {ticket.approval?.branches?.length ? <section aria-label="Departmental approvals" style={{ marginTop: 24 }}><h2 style={{ fontFamily: "Georgia, serif", fontWeight: 400 }}>Departmental approvals</h2><div style={{ display: "grid", gap: 12 }}>{ticket.approval.branches.map(branch => <article key={branch.branch_id} style={{ border: `1px solid ${branch.status === "approved" ? "#b7ddc5" : colors.border}`, borderRadius: 6, padding: 16 }}><strong>{branch.department}</strong><span style={{ marginLeft: 10, color: colors.muted, fontSize: 12 }}>Approver: {branch.owner} · {branch.status.replaceAll("_", " ")}</span><p><strong>Original requirement</strong><br />{branch.requirements}</p>{branch.warnings.map((warning, index) => <p key={`${branch.branch_id}-warning-${index}`} role="alert" style={{ color: "#8a5a00" }}>Guardrail: {warning}</p>)}<pre style={{ whiteSpace: "pre-wrap", font: "inherit", lineHeight: 1.6 }}>{branch.draft}</pre>{branch.changelog.length > 1 ? <details><summary>Revision history ({branch.changelog.length})</summary>{branch.changelog.map((item, index) => <p key={`${branch.branch_id}-change-${index}`} style={{ color: colors.muted }}>Iteration {item.iteration}: {item.feedback || "Initial draft"}<br />{item.draft}</p>)}</details> : null}{branch.status === "waiting_for_approval" ? <><label style={{ display: "block", margin: "12px 0 8px", fontSize: 13 }}>Reviewer feedback (required to reject or request changes)<textarea value={approvalFeedback[branch.branch_id] ?? ""} onChange={event => setApprovalFeedback(current => ({ ...current, [branch.branch_id]: event.target.value }))} rows={3} style={{ display: "block", width: "100%", marginTop: 5, padding: 8, borderColor: colors.border }} /></label><div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>{(["approve", "request_changes", "reject"] as const).map(decision => <button key={decision} type="button" disabled={approvalBusy === branch.branch_id} onClick={() => void decideApproval(ticket.ticket_id, branch, decision)} style={{ border: 0, borderRadius: 4, padding: "9px 12px", background: decision === "approve" ? "#216e43" : decision === "reject" ? "#8b2525" : "#8a5a00", color: "white", cursor: "pointer" }}>{approvalBusy === branch.branch_id ? "Saving…" : decision.replaceAll("_", " ")}</button>)}</div></> : null}</article>)}</div>{ticket.approval.final_proposal ? <><h2 style={{ fontFamily: "Georgia, serif", fontWeight: 400 }}>Final proposal · all departments approved</h2><pre style={{ whiteSpace: "pre-wrap", font: "inherit", lineHeight: 1.6 }}>{JSON.stringify(ticket.approval.final_proposal, null, 2)}</pre></> : null}</section> : null}
        </article>) : <article style={{ border: `1px solid ${colors.border}`, borderRadius: 8, background: colors.surface, padding: 28, color: colors.muted }}>No RFP tickets yet. Upload a PDF to start an intake.</article>}</section>
      </main></div></div>;
}
