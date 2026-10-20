/** Wire-format types matching the tracker backend API exactly. */

export interface Note {
  id: string;
  record_id: string;
  content: string;
  created_at: string;
}

export interface Candidate {
  id: string;
  full_name: string;
  email: string;
  phone: string;
  position: string;
  experience_years: number;
  linkedin_url?: string | null;
  cv_url?: string | null;
  status: CandidateStatus;
  stage: CandidateStage;
  applied_at: string;
  updated_at: string;
  notes_count?: number;
  notes?: Note[];
}

export type CandidateStatus = "received" | "in_progress" | "selected" | "discarded";

export type CandidateStage =
  | "pending"
  | "review"
  | "personal_interview"
  | "technical_interview"
  | "offer_presented";

export type UIState = "loading" | "success" | "error";

export interface RecordsListResponse {
  total: number;
  page: number;
  limit: number;
  data: Candidate[];
}

export interface NotesListResponse {
  data: Note[];
  meta: { total: number };
}

export interface RecordCreatePayload {
  full_name: string;
  email: string;
  phone: string;
  position: string;
  experience_years: number;
  linkedin_url?: string | null;
  cv_url?: string | null;
}

export interface RecordPatchPayload {
  status?: CandidateStatus;
  stage?: CandidateStage;
}

export interface NoteCreatePayload {
  content: string;
}

export interface ApiError {
  detail?: Array<{ msg: string; loc: (string | number)[] }>;
  message?: string;
}

/** HealthCore People & Workforce UI labels mapped to backend enum values. */
export const STATUS_LABELS: Record<CandidateStatus, string> = {
  received: "Application Received",
  in_progress: "Active Review",
  selected: "Active Pipeline",
  discarded: "Rejected",
};

export const STAGE_LABELS: Record<CandidateStage, string> = {
  pending: "Initial Screening",
  review: "Credential Review",
  personal_interview: "Culture Fit Interview",
  technical_interview: "Clinical Skills Assessment",
  offer_presented: "Offer Extended",
};

export const ALL_STATUSES = Object.keys(STATUS_LABELS) as CandidateStatus[];
export const ALL_STAGES = Object.keys(STAGE_LABELS) as CandidateStage[];
