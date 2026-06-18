1. Collection Operations (src/utils/collections.ts)
filterClaims(claims: Claim[], filters: Partial<Pick<Claim, "locationId" | "status" | "payerName" | "serviceType">>): Claim[]

Returns claims that match ALL provided filter criteria
Ignores filter keys that are not provided
filterAppointmentsByStatus(appointments: Appointment[], status: AppointmentStatus[]): Appointment[]

Returns appointments whose status matches any of the provided statuses
sortClaimsById(claims: Claim[], direction: "asc" | "desc"): Claim[]

Returns claims sorted alphanumerically by claimId
Must not mutate the original array
sortAppointmentsByDate(appointments: Appointment[], direction: "asc" | "desc"): Appointment[]

Returns appointments sorted by scheduledDate
Must not mutate the original array
groupClaimsBy(claims: Claim[], key: "locationId" | "payerName" | "status" | "serviceType"): Record<string, Claim[]>

Groups claims by the specified key
Returns an object where each key maps to an array of matching claims