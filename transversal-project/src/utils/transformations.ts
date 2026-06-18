/* 3. Billing Denial Rate Calculator (src/utils/transformations.ts)
calculateDenialRate(claims: Claim[]): number

Returns the denial rate as a percentage (0–100), rounded to 2 decimal places
Only counts claims with status "denied" as denied
Throws an error if the claims array is empty
denialRateByPayer(claims: Claim[]): Record<string, number>

Groups claims by payerName and calculates the denial rate for each payer
Returns an object where keys are payer names and values are denial rate percentages (rounded to 2 decimal places)
Only includes payers that appear in the claims array
denialRateByLocation(claims: Claim[]): Record<string, number>

Groups claims by locationId and calculates the denial rate for each location
Returns an object where keys are location IDs and values are denial rate percentages (rounded to 2 decimal places)
flagHighDenialPayers(claims: Claim[], threshold: number): string[]

Returns the names of payers whose denial rate exceeds the given threshold
Use 8 as the default threshold (HealthCore's industry benchmark is 5–8%)
Returns an empty array if no payers exceed the threshold
*/

/*5. CME Compliance Tracker (src/utils/transformations.ts)
generateCMEReport(clinicians: Clinician[], asOfDate: string): CMEReport[]

Generates one report entry per clinician. Return type:
*/

/*getCliniciansAtRisk(clinicians: Clinician[], asOfDate: string): Clinician[]

Returns all clinicians whose complianceStatus is "at_risk" or "overdue"
getCliniciansWithExpiringLicences(clinicians: Clinician[], asOfDate: string, daysThreshold: number): Clinician[]

Returns clinicians whose licence expires within daysThreshold calendar days from asOfDate
Use 90 as the recommended threshold for first alerts, 30 for urgent alerts  
*/