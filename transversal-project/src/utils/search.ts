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