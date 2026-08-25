import { IncidentSummaryPanel } from "@/components/IncidentSummaryPanel";
import { getIncidentSummary, type IncidentSummary } from "@/lib/incidentApi";

export default async function IncidentSummaryPage() {
  let initialSummary: IncidentSummary | null = null;
  let initialError: string | null = null;

  try {
    initialSummary = await getIncidentSummary();
  } catch (err) {
    initialError = err instanceof Error ? err.message : "Summary could not be loaded.";
  }

  return (
    <div className="mx-auto w-full max-w-6xl">
      <IncidentSummaryPanel
        initialSummary={initialSummary}
        initialError={initialError}
      />
    </div>
  );
}
