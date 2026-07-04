import { apiRequest } from "@/services/api";
import type {
  Candidate,
  RecordCreatePayload,
  RecordPatchPayload,
  RecordsListResponse,
} from "@/types";

export async function fetchRecords(limit = 200): Promise<Candidate[]> {
  const response = await apiRequest<RecordsListResponse>(
    `/records?limit=${limit}`,
  );
  return response.data;
}

export async function fetchRecordById(id: string): Promise<Candidate> {
  return apiRequest<Candidate>(`/records/${id}`);
}

export async function createRecord(
  payload: RecordCreatePayload,
): Promise<Candidate> {
  return apiRequest<Candidate>("/records", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function replaceRecord(
  id: string,
  payload: RecordCreatePayload,
): Promise<Candidate> {
  return apiRequest<Candidate>(`/records/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function patchRecord(
  id: string,
  payload: RecordPatchPayload,
): Promise<Candidate> {
  return apiRequest<Candidate>(`/records/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
