import {
  calculateNoShowCost,
  denialRateByLocation,
  denialRateByPayer,
  flagHighDenialPayers,
  flagHighNoShowLocations,
  generateCMEReport,
  noShowRateByLocation,
} from "./utils/transformations";
import { filterClaims } from "./utils/collections";
import type { CMEReport, Claim } from "./types/models";
import {
  sampleAppointments,
  sampleClaims,
  sampleClinicians,
  sampleLocations,
} from "./types/sampleData";

export type OpsDashboardSnapshot = {
  generatedAt: string;
  claims: {
    total: number;
    denied: Claim[];
    denialRatesByPayer: Record<string, number>;
    denialRatesByLocation: Record<string, number>;
    highDenialPayers: string[];
  };
  noShows: {
    ratesByLocation: Record<string, number>;
    highNoShowLocations: string[];
    weeklyCosts: Array<{
      locationId: string;
      locationName: string;
      weekEndingDate: string;
      noShowCostUsd: number;
      noShowRate: number;
    }>;
  };
  cme: {
    asOfDate: string;
    atRisk: CMEReport[];
    overdue: CMEReport[];
  };
};

const DEFAULT_WEEK_ENDING = "2025-03-14";
const DEFAULT_CME_AS_OF = "2026-06-19";

/**
 * Executes the shared Milestone 2 operations against sample data and returns
 * structured results for UI rendering (no console output).
 */
export function buildOpsDashboardSnapshot(
  weekEndingDate: string = DEFAULT_WEEK_ENDING,
  cmeAsOfDate: string = DEFAULT_CME_AS_OF
): OpsDashboardSnapshot {
  const denialRatesByPayer = denialRateByPayer(sampleClaims);
  const denialRatesByLocation = denialRateByLocation(sampleClaims);
  const ratesByLocation = noShowRateByLocation(sampleAppointments);
  const cmeReports = generateCMEReport(sampleClinicians, cmeAsOfDate);

  const weeklyCosts = sampleLocations.map((location) => ({
    locationId: location.locationId,
    locationName: location.name,
    weekEndingDate,
    noShowCostUsd: calculateNoShowCost(sampleAppointments, location, weekEndingDate),
    noShowRate: ratesByLocation[location.locationId] ?? 0,
  }));

  return {
    generatedAt: new Date().toISOString(),
    claims: {
      total: sampleClaims.length,
      denied: filterClaims(sampleClaims, { status: "denied" }),
      denialRatesByPayer,
      denialRatesByLocation,
      highDenialPayers: flagHighDenialPayers(sampleClaims),
    },
    noShows: {
      ratesByLocation,
      highNoShowLocations: flagHighNoShowLocations(sampleAppointments),
      weeklyCosts,
    },
    cme: {
      asOfDate: cmeAsOfDate,
      atRisk: cmeReports.filter((report) => report.complianceStatus === "at_risk"),
      overdue: cmeReports.filter((report) => report.complianceStatus === "overdue"),
    },
  };
}

export * from "./types/models";
export * from "./types/sampleData";
export * from "./utils/collections";
export * from "./utils/search";
export * from "./utils/transformations";
export * from "./utils/validations";
