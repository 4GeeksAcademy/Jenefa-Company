const API_BASE =
  process.env.NEXT_PUBLIC_INCIDENT_API_URL?.replace(/\/$/, "") ||
  "/backend";
import { apiFetch, API_BASE, readJson } from "@/lib/api";

export type IncidentAnalysis = {
  source_file: string;
  total_records: number;
  valid_records: number;
  invalid_records: number;
  invalid_breakdown: Record<string, number>;
  invalid_breakdown_labels?: Record<string, string>;
  by_category: Record<string, number>;
  by_status: Record<string, number>;
  by_country: Record<string, number>;
  satisfaction: {
    scored_cases: number;
    closed_cases: number;
    average: number | null;
    counts: Record<string, number>;
  };
  error?: string | null;
};

export async function analyzeIncidentFile(file: File): Promise<IncidentAnalysis> {
  const body = new FormData();
  body.append("file", file);

  const response = await apiFetch("/api/incidents/analyze", {
    method: "POST",
    body,
  });

  return readJson<IncidentAnalysis>(response);
}

export function exportResultsUrl(): string {
  return `${API_BASE}/api/incidents/results/export`;
}
