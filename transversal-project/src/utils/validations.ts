/*4. No-Show Cost Estimator (src/utils/transformations.ts)
calculateNoShowCost(appointments: Appointment[], location: Location, weekEndingDate: string): number

Calculates the total estimated revenue lost to no-shows at a given location during the 7 calendar days ending on weekEndingDate (inclusive)
Uses location.averageConsultationFee[serviceType] to estimate the cost of each missed appointment
Returns 0 if there are no no-shows in that period
Returns a number in USD, rounded to 2 decimal places
noShowRateByLocation(appointments: Appointment[]): Record<string, number>

Calculates the no-show rate per location as a percentage
Returns an object where keys are location IDs and values are percentages (rounded to 2 decimal places)
flagHighNoShowLocations(appointments: Appointment[], threshold: number): string[]

Returns the IDs of locations whose no-show rate exceeds the given threshold
Use 20 as the default threshold (HealthCore's internal alert level)
*/

/* 6. Validations (src/utils/validations.ts)
validateClaim(claim: Claim, knownLocationIds: string[]): { valid: boolean, errors: string[] }

Validates all business rules for a claim
Returns { valid: true, errors: [] } if all rules pass
Returns { valid: false, errors: ["..."] } with one message per failed rule
validateClinician(clinician: Clinician): { valid: boolean, errors: string[] }

Validates all business rules for a clinician record
Returns { valid: true, errors: [] } if all rules pass
isDenialRateAboveThreshold(rate: number, threshold?: number): boolean

Returns true if rate exceeds threshold (default: 8)
isNoShowRateAboveThreshold(rate: number, threshold?: number): boolean

Returns true if rate exceeds threshold (default: 20)
*/