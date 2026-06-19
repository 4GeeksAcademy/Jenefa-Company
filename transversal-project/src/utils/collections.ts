/* 1. Collection Operations (src/utils/collections.ts)

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
*/
import { Claim, Appointment, AppointmentStatus } from "../types/models";

function getDirectionMultiplier(direction: "asc" | "desc"): number {
  return direction === "asc" ? 1 : -1;
}

export function filterClaims(
  claims: Claim[], 
  filters: Partial<Pick<Claim, "locationId" | "status" | "payerName" | "serviceType">>
): Claim[] {
  return claims.filter(claim => {
    return Object.entries(filters).every(([key, value]) => {
      if (value === undefined) return true;
      return claim[key as keyof typeof filters] === value;
    });
  });
}

export function filterAppointmentsByStatus(
  appointments: Appointment[], 
  status: AppointmentStatus[]
): Appointment[] {
  if (status.length === 0) return [];
  return appointments.filter(appointment => status.includes(appointment.status));
}

export function sortClaimsById(claims: Claim[], direction: "asc" | "desc"): Claim[] {
  const multiplier = getDirectionMultiplier(direction);
  return [...claims].sort((a, b) => {
    return a.claimId.localeCompare(b.claimId) * multiplier;
  });
}

export function sortAppointmentsByDate(appointments: Appointment[], direction: "asc" | "desc"): Appointment[] {
  const multiplier = getDirectionMultiplier(direction);
  return [...appointments].sort((a, b) => { 
    return (new Date(a.scheduledDate).getTime() - new Date(b.scheduledDate).getTime()) * multiplier;
  });
}

export function groupClaimsBy(
  claims: Claim[], 
  key: "locationId" | "payerName" | "status" | "serviceType"
): Record<string, Claim[]> {
  return claims.reduce<Record<string, Claim[]>>((accumulator, claim) => {
    const groupValue = claim[key];
    if (!accumulator[groupValue]) {
      accumulator[groupValue] = [];
    }
    accumulator[groupValue].push(claim);
    return accumulator;
  }, {});
}