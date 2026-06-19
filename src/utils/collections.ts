
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

// Filtering appointments by status
export function filterAppointmentsByStatus(
  appointments: Appointment[], 
  status: AppointmentStatus[]
): Appointment[] {
  if (status.length === 0) return [];
  return appointments.filter(appointment => status.includes(appointment.status));
}

//Sorting claims and appointments
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

// Grouping claims by a specific key 
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