// Interface representing a healthcare claim
interface Claim {
  claimId: string; // Format: "CLM-XXXXXX" (e.g., "CLM-000042")
  patientId: string; // Format: "HC-XXXXXX" (e.g., "HC-A3F291")
  locationId: string; // Clinic ID (e.g., "us-tx-001")
  serviceType: ServiceType; // Type of care delivered
  payerName: string; // Insurance provider name (e.g., "BlueCross")
  payerId: string; // Alphanumeric payer code
  submissionDate: string; // ISO 8601 date string
  claimAmount: number; // Amount billed in USD (must be > 0)
  status: ClaimStatus; // Current claim status
  denialReason?: DenialReason; // Only present when status === "denied"
  resubmitted: boolean; // Whether the claim was resubmitted after denial
}
type ClaimStatus = "submitted" | "approved" | "denied" | "pending" | "appealed";

type DenialReason =
  | "missing_authorisation"
  | "coding_error"
  | "duplicate_claim"
  | "patient_not_covered"
  | "service_not_covered"
  | "incomplete_documentation";

type ServiceType =
  | "primary_care"
  | "chronic_disease"
  | "preventive"
  | "specialist"
  | "womens_health"
  | "paediatric"
  | "mental_health";

// Interface representing a healthcare appointment
interface Appointment {
  appointmentId: string; // Format: "APT-XXXXXX"
  patientId: string; // Format: "HC-XXXXXX"
  locationId: string; // Clinic ID
  serviceType: ServiceType; // Type of care scheduled
  scheduledDate: string; // ISO 8601 date string
  scheduledTime: string; // "HH:MM" in 24-hour format
  status: AppointmentStatus; // Current appointment status
  noShowReason?: string; // Free text, only present when status === "no_show"
  confirmedAt?: string; // ISO 8601 datetime, absent if not yet confirmed
}

type AppointmentStatus =
  | "scheduled"
  | "confirmed"
  | "completed"
  | "no_show"
  | "cancelled";

  interface Clinician {
  clinicianId: string; // Format: "CLN-XXXXXX"
  firstName: string;
  lastName: string;
  role: ClinicianRole; // Determines CME requirements
  locationId: string; // Assigned clinic
  licenceState: string; // US state code (e.g., "TX") or "UK"
  licenceExpiryDate: string; // ISO 8601 date string
  cmeHoursRequired: number; // Annual CME hours required for this role
  cmeHoursLogged: number; // Hours logged so far in the current cycle
  cmeYearStartDate: string; // ISO 8601 date — start of current CME cycle
}

type ClinicianRole =
  | "physician"
  | "nurse_practitioner"
  | "nurse"
  | "medical_assistant";

  // Interface representing a healthcare location (clinic)
  interface Location {
  locationId: string;
  name: string;
  city: string;
  stateOrCountry: string;
  country: "US" | "UK";
  phone: string;
  averageConsultationFee: Record<ServiceType, number>; // Average fee in USD per service type
}

// Interface representing a CME compliance report entry for a clinician
interface CMEReport {
  clinicianId: string;
  fullName: string; // "${firstName} ${lastName}"
  role: ClinicianRole;
  locationId: string;
  hoursRequired: number;
  hoursLogged: number;
  hoursRemaining: number; // Math.max(0, required - logged)
  percentComplete: number; // (logged / required) * 100, rounded to 1 decimal
  daysRemainingInCycle: number; // Calendar days from asOfDate to end of CME cycle
  complianceStatus: CMEStatus;
  licenceExpiryDate: string;
  licenceDaysRemaining: number; // Calendar days from asOfDate to licence expiry
}

type CMEStatus = "on_track" | "at_risk" | "overdue" | "complete";