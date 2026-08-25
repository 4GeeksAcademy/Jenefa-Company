import Link from "next/link";

export default function IncidentsPage() {
  return (
    <div className="mx-auto w-full max-w-5xl border border-border bg-surface px-6 py-7">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">
        Incident management
      </p>
      <h2 className="mt-2 font-display text-3xl text-foreground">Central incident workspace</h2>
      <p className="mt-3 text-sm text-muted">
        Choose a module to create incidents, triage active items, or review aggregate metrics.
      </p>

      <div className="mt-6 grid gap-3 md:grid-cols-3">
        <Link
          href="/incidents/register"
          className="border border-border bg-white px-4 py-3 text-sm text-foreground hover:bg-background"
        >
          Open registration form
        </Link>
        <Link
          href="/incidents/list"
          className="border border-border bg-white px-4 py-3 text-sm text-foreground hover:bg-background"
        >
          Open list panel
        </Link>
        <Link
          href="/incidents/summary"
          className="border border-border bg-white px-4 py-3 text-sm text-foreground hover:bg-background"
        >
          Open summary panel
        </Link>
      </div>
    </div>
  );
}
