
import { Claim, Clinician } from "../types/models";


// Generic function to find the first match
function findFirstMatch<T>(items: T[], predicate: (item: T) => boolean): T | null {
  for (const item of items) {
    if (predicate(item)) {
      return item;
    }
  }
  return null;
}

export function findClaimById(claims: Claim[], claimId: string): Claim | null {
  return findFirstMatch(claims, (claim) => claim.claimId === claimId);
}


export function findClinicianById(clinicians: Clinician[], clinicianId: string): Clinician | null {
  return findFirstMatch(clinicians, (clinician) => clinician.clinicianId === clinicianId);
}
// Binary search for claims by claimId 
export function binarySearchClaimById(sortedClaims: Claim[], targetId: string): number {
  let low = 0;
  let high = sortedClaims.length - 1;

  while (low <= high) {
    const mid = Math.floor(low + (high - low) / 2);
    const midId = sortedClaims[mid].claimId;

    if (midId === targetId) {
      return mid; 
    }
    if (midId < targetId) {
      low = mid + 1; 
    } else {
      high = mid - 1; 
    }
  }
  return -1; 
}