import { ReportingRefresh } from "@/components/ReportingRefresh";

export default function ReportingPage() {
  return (
    <div className="mx-auto w-full max-w-6xl">
      <div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Business logic</p>
          <h1 className="mt-2 font-display text-4xl text-foreground">Business reporting</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">Live executive performance rows from the latest completed reporting pipeline run.</p>
        </div>
      </div>
      <div className="mt-8">
        <ReportingRefresh />
      </div>
    </div>
  );
}