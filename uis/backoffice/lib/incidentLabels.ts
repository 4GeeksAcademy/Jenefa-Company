import {
  type IncidentBranch,
  type IncidentCategory,
  type IncidentOrigin,
  type IncidentStatus,
} from "@/lib/incidentApi";

export const CATEGORY_LABELS: Record<IncidentCategory, string> = {
  clinical_operations: "Clinical operations",
  patient_experience: "Patient experience",
  revenue_cycle: "Revenue cycle",
  compliance_governance: "Compliance governance",
  people_workforce: "People & workforce",
  technology: "Technology",
};

export const STATUS_LABELS: Record<IncidentStatus, string> = {
  open: "Open",
  in_progress: "In progress",
  resolved: "Resolved",
  discarded: "Discarded",
};

export const ORIGIN_LABELS: Record<IncidentOrigin, string> = {
  customer: "Customer",
  branch: "Branch",
  internal: "Internal",
};

export const BRANCH_LABELS: Record<IncidentBranch, string> = {
  texas_clinic_1: "Texas Clinic 1",
  texas_clinic_2: "Texas Clinic 2",
  texas_clinic_3: "Texas Clinic 3",
  florida_clinic_1: "Florida Clinic 1",
  florida_clinic_2: "Florida Clinic 2",
  florida_clinic_3: "Florida Clinic 3",
  georgia_clinic_1: "Georgia Clinic 1",
  georgia_clinic_2: "Georgia Clinic 2",
  georgia_clinic_3: "Georgia Clinic 3",
  london_clinic_1: "London Clinic 1",
  london_clinic_2: "London Clinic 2",
  manchester_clinic: "Manchester Clinic",
  central: "Central backbone",
};
