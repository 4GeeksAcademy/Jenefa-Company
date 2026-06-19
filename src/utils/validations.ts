

import { Claim, Clinician } from "../types/models";

const PATIENT_ID_REGEX = /^HC-[A-Z0-9]{6}$/;
const VALID_CLINICIAN_ROLES = new Set([
  "physician",
  "nurse_practitioner",
  "nurse",
  "medical_assistant",
]);

// Validation function for claims
export function validateClaim(
  claim: Claim,
  knownLocationIds: string[]
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (claim.claimAmount <= 0) {
    errors.push("Claim amount must be greater than 0.");
  }

  const submissionDate = new Date(claim.submissionDate);
  const isSubmissionDateValid = !Number.isNaN(submissionDate.getTime());
  if (!isSubmissionDateValid) {
    errors.push("Submission date must be a valid ISO date.");
  } else {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    submissionDate.setHours(0, 0, 0, 0);
    if (submissionDate.getTime() > today.getTime()) {
      errors.push("Submission date must not be in the future.");
    }
  }

  if (!knownLocationIds.includes(claim.locationId)) {
    errors.push(`Location ID '${claim.locationId}' is invalid or unknown.`);
  }

  if (claim.status === "denied" && !claim.denialReason) {
    errors.push("Denied claims must include a denial reason.");
  }

  if (!PATIENT_ID_REGEX.test(claim.patientId)) {
    errors.push("Patient ID must follow format HC- followed by 6 alphanumeric characters.");
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

// Validation function for clinicians
export function validateClinician(clinician: Clinician): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (clinician.cmeHoursRequired < 0) {
    errors.push("CME hours required must be greater than or equal to 0.");
  }

  if (clinician.cmeHoursLogged < 0) {
    errors.push("CME hours logged must be greater than or equal to 0.");
  }

  if (!VALID_CLINICIAN_ROLES.has(clinician.role)) {
    errors.push("Clinician role is invalid.");
  }

  const licenceExpiryDate = new Date(clinician.licenceExpiryDate);
  if (Number.isNaN(licenceExpiryDate.getTime())) {
    errors.push("Licence expiry date must be a valid ISO date.");
  } else {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    licenceExpiryDate.setHours(0, 0, 0, 0);
    if (licenceExpiryDate.getTime() < today.getTime()) {
      errors.push("Licence is expired.");
    }
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

export function isDenialRateAboveThreshold(rate: number, threshold: number = 8): boolean {
  return rate > threshold;
}

export function isNoShowRateAboveThreshold(rate: number, threshold: number = 20): boolean {
  return rate > threshold;
}