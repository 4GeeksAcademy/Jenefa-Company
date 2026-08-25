import { IncidentListPanel } from "@/components/IncidentListPanel";
import { listIncidents, type Incident } from "@/lib/incidentApi";

export default async function IncidentListPage() {
  let initialItems: Incident[] = [];
  let initialError: string | null = null;

  try {
    const response = await listIncidents({});
    initialItems = response.items;
  } catch (err) {
    initialError = err instanceof Error ? err.message : "Unable to load incidents.";
  }

  return (
    <div className="mx-auto w-full max-w-6xl">
      <IncidentListPanel initialItems={initialItems} initialError={initialError} />
    </div>
  );
}
