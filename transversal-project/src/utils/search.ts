/*2. Search Operations (src/utils/search.ts)

findClaimById(claims: Claim[], claimId: string): Claim | null
Performs linear search to find a claim by its ID
Returns the claim if found, null otherwise

findClinicianById(clinicians: Clinician[], clinicianId: string): Clinician | null
Performs linear search to find a clinician by their ID
Returns the clinician if found, null otherwise

binarySearchClaimById(sortedClaims: Claim[], targetId: string): number
Assumes the array is already sorted by claimId ascending (use sortClaimsById first)
Performs binary search to find the index of the claim with the target ID
Returns the index if found, -1 otherwise
*/
import { Claim, Clinician } from "../types/models";

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