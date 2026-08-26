const API_BASE =
  process.env.NEXT_PUBLIC_INCIDENT_API_URL?.replace(/\/$/, "") ||
  "/backend";

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

export type ApiError = {
  error: string;
  detail: string;
};

export async function analyzeIncidentFile(
  file: File
): Promise<IncidentAnalysis> {
  const body = new FormData();
  body.append("file", file);

  const response = await fetch(`${API_BASE}/api/incidents/analyze`, {
    method: "POST",
    body,
  });

  const payload = (await response.json()) as IncidentAnalysis | ApiError;
  if (!response.ok) {
    const detail =
      "detail" in payload ? payload.detail : "Unable to analyze the upload.";
    throw new Error(detail);
  }
  return payload as IncidentAnalysis;
}

export function exportResultsUrl(): string {
  return `${API_BASE}/api/incidents/results/export`;
}
