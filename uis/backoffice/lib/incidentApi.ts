const API_BASE =
  process.env.NEXT_PUBLIC_INCIDENT_API_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

export const INCIDENT_CATEGORIES = [
  "clinical_operations",
  "patient_experience",
  "revenue_cycle",
  "compliance_governance",
  "people_workforce",
  "technology",
] as const;

export const INCIDENT_STATUSES = [
  "open",
  "in_progress",
  "resolved",
  "discarded",
] as const;

export const INCIDENT_ORIGINS = ["customer", "branch", "internal"] as const;

export const INCIDENT_BRANCHES = [
  "texas_clinic_1",
  "texas_clinic_2",
  "texas_clinic_3",
  "florida_clinic_1",
  "florida_clinic_2",
  "florida_clinic_3",
  "georgia_clinic_1",
  "georgia_clinic_2",
  "georgia_clinic_3",
  "london_clinic_1",
  "london_clinic_2",
  "manchester_clinic",
  "central",
] as const;

export type IncidentCategory = (typeof INCIDENT_CATEGORIES)[number];
export type IncidentStatus = (typeof INCIDENT_STATUSES)[number];
export type IncidentOrigin = (typeof INCIDENT_ORIGINS)[number];
export type IncidentBranch = (typeof INCIDENT_BRANCHES)[number];

export type Incident = {
  id: number;
  title: string;
  description: string;
  category: IncidentCategory;
  status: IncidentStatus;
  origin: IncidentOrigin;
  branch: IncidentBranch;
  created_at: string;
  updated_at: string;
};

export type IncidentCreateInput = {
  title: string;
  description: string;
  category: IncidentCategory;
  status: IncidentStatus;
  origin: IncidentOrigin;
  branch: IncidentBranch;
};

export type IncidentSummary = {
  status: Record<IncidentStatus, number>;
  category: Record<IncidentCategory, number>;
  origin: Record<IncidentOrigin, number>;
  branch: Record<IncidentBranch, number>;
};

export type ApiError = {
  error: string;
  detail: string;
  field_errors?: Record<string, string>;
};

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH";
  body?: unknown;
};

async function requestJson<T>(path: string, options?: RequestOptions): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: options?.method ?? "GET",
    headers: options?.body ? { "Content-Type": "application/json" } : undefined,
    body: options?.body ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
  });

  const payload = (await response.json()) as T | ApiError;
  if (!response.ok) {
    const detail =
      "detail" in payload ? payload.detail : "The request could not be completed.";
    const err = new Error(detail) as Error & { fieldErrors?: Record<string, string> };
    if ("field_errors" in payload && payload.field_errors) {
      err.fieldErrors = payload.field_errors;
    }
    throw err;
  }

  return payload as T;
}

export async function createIncident(input: IncidentCreateInput): Promise<Incident> {
  return requestJson<Incident>("/api/incidents", {
    method: "POST",
    body: input,
  });
}

export async function listIncidents(filters: {
  status?: IncidentStatus | "";
  origin?: IncidentOrigin | "";
  branch?: IncidentBranch | "";
  category?: IncidentCategory | "";
}): Promise<{ items: Incident[]; count: number }> {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.origin) params.set("origin", filters.origin);
  if (filters.branch) params.set("branch", filters.branch);
  if (filters.category) params.set("category", filters.category);

  const query = params.toString();
  return requestJson<{ items: Incident[]; count: number }>(
    `/api/incidents${query ? `?${query}` : ""}`
  );
}

export async function updateIncidentStatus(
  incidentId: number,
  status: IncidentStatus
): Promise<Incident> {
  return requestJson<Incident>(`/api/incidents/${incidentId}/status`, {
    method: "PATCH",
    body: { status },
  });
}

export async function getIncidentSummary(): Promise<IncidentSummary> {
  return requestJson<IncidentSummary>("/api/incidents/summary");
}
