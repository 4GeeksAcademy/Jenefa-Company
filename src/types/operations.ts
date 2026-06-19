import { filterClaims } from "../utils/collections";
import { findClinicianById } from "../utils/search";
import {
  calculateNoShowCost,
  denialRateByLocation,
  denialRateByPayer,
  generateCMEReport,
  noShowRateByLocation,
} from "../utils/transformations";
import { Claim, CMEStatus } from "./models";
import {
  sampleAppointments,
  sampleClaims,
  sampleClinicians,
  sampleLocations,
} from "./sampleData";

type ArgMap = Record<string, string>;

function parseArgs(argv: string[]): { command: string; args: ArgMap } {
  const command = argv[2] || "help";
  const args: ArgMap = {};

  for (let i = 3; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) {
      continue;
    }

    const key = token.slice(2);
    const value = argv[i + 1];
    if (value && !value.startsWith("--")) {
      args[key] = value;
      i += 1;
    } else {
      args[key] = "true";
    }
  }

  return { command, args };
}

function printResult(label: string, payload: unknown): void {
  console.log(`\n${label}`);
  console.log(JSON.stringify(payload, null, 2));
}

function printHelp(): void {
  console.log("HealthCore terminal operations");
  console.log("\nCommands:");
  console.log(
    "- filter --locationId <id> --payerName <name> --status <status> --serviceType <type>"
  );
  console.log("- search-clinician --clinicianId <id>");
  console.log("- denial-payer --payerName <name>");
  console.log("- denial-location --locationId <id>");
  console.log("- no-show --locationId <id> --weekEndingDate <YYYY-MM-DD> --threshold <number>");
  console.log("- cme --status <at_risk|overdue> --asOfDate <YYYY-MM-DD>");
}

function run(): void {
  const { command, args } = parseArgs(process.argv);

  if (command === "filter") {
    const filtered = filterClaims(sampleClaims, {
      locationId: args.locationId,
      payerName: args.payerName,
      status: args.status as Claim["status"] | undefined,
      serviceType: args.serviceType as Claim["serviceType"] | undefined,
    });
    printResult("Filtered claims", filtered);
    return;
  }

  if (command === "search-clinician") {
    const clinician = args.clinicianId
      ? findClinicianById(sampleClinicians, args.clinicianId)
      : null;
    printResult("Clinician search result", clinician);
    return;
  }

  if (command === "denial-payer") {
    const rates = denialRateByPayer(sampleClaims);
    if (args.payerName) {
      printResult("Denial rate by payer", {
        payerName: args.payerName,
        denialRate: rates[args.payerName] ?? 0,
      });
      return;
    }

    printResult("Denial rates by payer", rates);
    return;
  }

  if (command === "denial-location") {
    const rates = denialRateByLocation(sampleClaims);
    if (args.locationId) {
      printResult("Denial rate by location", {
        locationId: args.locationId,
        denialRate: rates[args.locationId] ?? 0,
      });
      return;
    }

    printResult("Denial rates by location", rates);
    return;
  }

  if (command === "no-show") {
    const location = sampleLocations.find((item) => item.locationId === args.locationId) || null;
    const weekEndingDate = args.weekEndingDate || "2025-03-14";
    const threshold = Number(args.threshold || "20");

    if (!location) {
      printResult("No-show report", { error: "Unknown locationId." });
      return;
    }

    const noShowRateMap = noShowRateByLocation(sampleAppointments);
    const locationRate = noShowRateMap[location.locationId] ?? 0;
    const noShowCost = calculateNoShowCost(sampleAppointments, location, weekEndingDate);

    printResult("No-show report", {
      locationId: location.locationId,
      weekEndingDate,
      noShowCostUsd: noShowCost,
      noShowRate: locationRate,
      exceedsThreshold: locationRate > threshold,
      threshold,
    });
    return;
  }

  if (command === "cme") {
    const status = (args.status as CMEStatus) || "at_risk";
    const asOfDate = args.asOfDate || "2026-06-19";
    const filtered = generateCMEReport(sampleClinicians, asOfDate).filter(
      (report) => report.complianceStatus === status
    );

    printResult("CME report by compliance status", {
      status,
      asOfDate,
      clinicians: filtered,
    });
    return;
  }

  printHelp();
}

run();