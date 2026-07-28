import {
  Appointment,
  Claim,
  Clinician,
  CMEReport,
  CMEStatus,
  Location,
} from "../types/models";

const MS_PER_DAY = 24 * 60 * 60 * 1000;

function toUtcDayStartMs(dateStr: string): number {
  const date = new Date(dateStr);
  if (Number.isNaN(date.getTime())) {
    return Number.NaN;
  }

  return Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate());
}

function getWeekWindowBoundsMs(weekEndingDate: string): { startMs: number; endMs: number } | null {
  const windowEndStartMs = toUtcDayStartMs(weekEndingDate);
  if (Number.isNaN(windowEndStartMs)) {
    return null;
  }

  const startMs = windowEndStartMs - 6 * MS_PER_DAY;
  const endMs = windowEndStartMs + MS_PER_DAY - 1;
  return { startMs, endMs };
}

function groupBy<T>(items: T[], keySelector: (item: T) => string): Record<string, T[]> {
  return items.reduce<Record<string, T[]>>((accumulator, item) => {
    const key = keySelector(item);
    if (!accumulator[key]) {
      accumulator[key] = [];
    } 
    accumulator[key].push(item);
    return accumulator;
  }, {});
}

function calculateDenialRateByKey(
  claims: Claim[],
  keySelector: (claim: Claim) => string
): Record<string, number> {
  const grouped = groupBy(claims, keySelector);
  const rates: Record<string, number> = {};

  for (const key in grouped) {
    rates[key] = calculateDenialRate(grouped[key]);
  }

  return rates;
}

function keysAboveThreshold(values: Record<string, number>, threshold: number): string[] {
  return Object.keys(values).filter((key) => values[key] > threshold);
}

// Function to get the difference in calendar days between two dates
function getCalendarDaysDiff(fromDateStr: string, toDateStr: string): number {
  const fromDate = new Date(fromDateStr);
  const toDate = new Date(toDateStr);

  fromDate.setHours(0, 0, 0, 0);
  toDate.setHours(0, 0, 0, 0);

  return (toDate.getTime() - fromDate.getTime()) / MS_PER_DAY;
}

function roundToDecimals(value: number, decimals: number): number {
  const factor = Math.pow(10, decimals);
  return Math.round((value + Number.EPSILON) * factor) / factor;
}

// Function to calculate CME cycle end date based on start date
function getCmeCycleEndDate(cmeYearStartDate: string): string {
  const cycleStart = new Date(cmeYearStartDate);
  const cycleEnd = new Date(cycleStart);
  cycleEnd.setFullYear(cycleEnd.getFullYear() + 1);
  cycleEnd.setDate(cycleEnd.getDate() - 1);
  return cycleEnd.toISOString().slice(0, 10);
}

export function calculateDenialRate(claims: Claim[]): number {
  if (claims.length === 0) {
    throw new Error("Claims array cannot be empty.");
  }

  const deniedCount = claims.filter((claim) => claim.status === "denied").length;
  return roundToDecimals((deniedCount / claims.length) * 100, 2);
}

export function denialRateByPayer(claims: Claim[]): Record<string, number> {
  return calculateDenialRateByKey(claims, (claim) => claim.payerName);
}

export function denialRateByLocation(claims: Claim[]): Record<string, number> {
  return calculateDenialRateByKey(claims, (claim) => claim.locationId);
}

export function flagHighDenialPayers(claims: Claim[], threshold: number = 8): string[] {
  if (claims.length === 0) {
    return [];
  }

  return keysAboveThreshold(denialRateByPayer(claims), threshold);
}

// No-show cost calculations
export function calculateNoShowCost(
  appointments: Appointment[],
  location: Location,
  weekEndingDate: string
): number {
  const bounds = getWeekWindowBoundsMs(weekEndingDate);
  if (!bounds) {
    return 0;
  }
  const { startMs: windowStartMs, endMs: windowEndMs } = bounds;

  let totalCost = 0;
  for (const appointment of appointments) {
    if (appointment.locationId !== location.locationId) {
      continue;
    }

    if (appointment.status !== "no_show") {
      continue;
    }

    const appointmentDateMs = new Date(appointment.scheduledDate).getTime();
    if (Number.isNaN(appointmentDateMs)) {
      continue;
    }

    if (appointmentDateMs < windowStartMs || appointmentDateMs > windowEndMs) {
      continue;
    }

    totalCost += location.averageConsultationFee[appointment.serviceType];
  }


  return Math.round(totalCost * 100) / 100;
}

export function noShowRateForLocationInWeek(
  appointments: Appointment[],
  locationId: string,
  weekEndingDate: string
): number {
  const bounds = getWeekWindowBoundsMs(weekEndingDate);
  if (!bounds) {
    return 0;
  }

  const { startMs, endMs } = bounds;
  let total = 0;
  let noShows = 0;

  for (const appointment of appointments) {
    if (appointment.locationId !== locationId) {
      continue;
    }

    const appointmentDateMs = new Date(appointment.scheduledDate).getTime();
    if (Number.isNaN(appointmentDateMs) || appointmentDateMs < startMs || appointmentDateMs > endMs) {
      continue;
    }

    total += 1;
    if (appointment.status === "no_show") {
      noShows += 1;
    }
  }

  if (total === 0) {
    return 0;
  }

  return roundToDecimals((noShows / total) * 100, 2);
}

export function noShowRateByLocation(appointments: Appointment[]): Record<string, number> {
  const totalByLocation: Record<string, number> = {};
  const noShowByLocation: Record<string, number> = {};

  for (const appointment of appointments) {
    totalByLocation[appointment.locationId] = (totalByLocation[appointment.locationId] || 0) + 1;
    if (appointment.status === "no_show") {
      noShowByLocation[appointment.locationId] = (noShowByLocation[appointment.locationId] || 0) + 1;
    }
  }

  const rates: Record<string, number> = {};
  for (const locationId in totalByLocation) {
    const total = totalByLocation[locationId];
    const noShows = noShowByLocation[locationId] || 0;
    rates[locationId] = roundToDecimals((noShows / total) * 100, 2);
  }

  return rates;
}

export function flagHighNoShowLocations(
  appointments: Appointment[],
  threshold: number = 20
): string[] {
  return keysAboveThreshold(noShowRateByLocation(appointments), threshold);
}

// CME Report generation and clinician risk checks
export function generateCMEReport(clinicians: Clinician[], asOfDate: string): CMEReport[] {
  return clinicians.map((clinician) => {
    const hoursRequired = clinician.cmeHoursRequired;
    const hoursLogged = clinician.cmeHoursLogged;
    const hoursRemaining = Math.max(0, hoursRequired - hoursLogged);
    const percentComplete = roundToDecimals(
      hoursRequired === 0 ? 100 : (hoursLogged / hoursRequired) * 100,
      1
    );

    const cycleStart = clinician.cmeYearStartDate;
    const cycleEnd = getCmeCycleEndDate(cycleStart);
    const daysRemainingInCycle = getCalendarDaysDiff(asOfDate, cycleEnd);
    const totalCycleDays = Math.max(1, getCalendarDaysDiff(cycleStart, cycleEnd) + 1);
    const elapsedCycleDays = Math.min(
      totalCycleDays,
      Math.max(0, getCalendarDaysDiff(cycleStart, asOfDate) + 1)
    );
    const elapsedShare = (elapsedCycleDays / totalCycleDays) * 100;
    const licenceDaysRemaining = getCalendarDaysDiff(asOfDate, clinician.licenceExpiryDate);

    let complianceStatus: CMEStatus;
    if (hoursLogged >= hoursRequired) {
      complianceStatus = "complete";
    } else if (daysRemainingInCycle < 0) {
      complianceStatus = "overdue";
    } else if (elapsedShare - percentComplete > 15) {
      complianceStatus = "at_risk";
    } else {
      complianceStatus = "on_track";
    }

    return {
      clinicianId: clinician.clinicianId,
      fullName: `${clinician.firstName} ${clinician.lastName}`,
      role: clinician.role,
      locationId: clinician.locationId,
      hoursRequired,
      hoursLogged,
      hoursRemaining,
      percentComplete,
      daysRemainingInCycle,
      complianceStatus,
      licenceExpiryDate: clinician.licenceExpiryDate,
      licenceDaysRemaining,
    };
  });
}

// Function to identify clinicians at risk licences
export function getCliniciansAtRisk(clinicians: Clinician[], asOfDate: string): Clinician[] {
  const riskyClinicianIds = new Set(
    generateCMEReport(clinicians, asOfDate)
      .filter(
        (report) => report.complianceStatus === "at_risk" || report.complianceStatus === "overdue"
      )
      .map((report) => report.clinicianId)
  );

  return clinicians.filter((clinician) => riskyClinicianIds.has(clinician.clinicianId));
}
// Function to identify clinicians with expiring licence
export function getCliniciansWithExpiringLicences(
  clinicians: Clinician[],
  asOfDate: string,
  daysThreshold: number
): Clinician[] {
  return clinicians.filter((clinician) => {
    const daysUntilExpiry = getCalendarDaysDiff(asOfDate, clinician.licenceExpiryDate);
    return daysUntilExpiry >= 0 && daysUntilExpiry <= daysThreshold;
  });
}