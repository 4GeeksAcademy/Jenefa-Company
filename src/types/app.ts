import { filterClaims, groupClaimsBy } from "../utils/collections";
import { findClinicianById } from "../utils/search";
import {
  calculateNoShowCost,
  denialRateByLocation,
  denialRateByPayer,
  generateCMEReport,
  noShowRateByLocation,
} from "../utils/transformations";
import { Claim, CMEStatus, ServiceType } from "./models";
import {
  sampleAppointments,
  sampleClaims,
  sampleClinicians,
  sampleLocations,
} from "./sampleData";

type FilterFields = Partial<Pick<Claim, "locationId" | "status" | "payerName" | "serviceType">>;

function uniqueBy<T, K extends keyof T>(items: T[], key: K): T[K][] {
  return [...new Set(items.map((item) => item[key]))];
}

function selectById(id: string): HTMLSelectElement {
  return document.getElementById(id) as HTMLSelectElement;
}

function inputById(id: string): HTMLInputElement {
  return document.getElementById(id) as HTMLInputElement;
}

function populateSelect(id: string, values: string[], includeAny: boolean = false): void {
  const select = selectById(id);
  const options: string[] = [];

  if (includeAny) {
    options.push('<option value="">Any</option>');
  }

  for (const value of values) {
    options.push(`<option value="${value}">${value}</option>`);
  }

  select.innerHTML = options.join("");
}

function initializeDropdowns(): void {
  populateSelect("filterLocation", uniqueBy(sampleClaims, "locationId") as string[], true);
  populateSelect("filterPayer", uniqueBy(sampleClaims, "payerName") as string[], true);
  populateSelect("filterStatus", uniqueBy(sampleClaims, "status") as string[], true);
  populateSelect("filterServiceType", uniqueBy(sampleClaims, "serviceType") as string[], true);

  populateSelect("clinicianIdSelect", uniqueBy(sampleClinicians, "clinicianId") as string[]);
  populateSelect("payerSelect", uniqueBy(sampleClaims, "payerName") as string[]);
  populateSelect("locationSelect", uniqueBy(sampleClaims, "locationId") as string[]);
  populateSelect("noShowLocation", uniqueBy(sampleLocations, "locationId") as string[]);
  populateSelect("weekEndingDate", uniqueBy(sampleAppointments, "scheduledDate") as string[]);
}

function clearConsole(): void {
  const outputElement = document.getElementById("output");
  if (outputElement) {
    outputElement.textContent = "";
  }
}

function appendToConsole(label: string, data?: unknown): void {
  const outputElement = document.getElementById("output");
  if (!outputElement) return;

  const entry = document.createElement("div");
  const hasData = typeof data !== "undefined";
  entry.textContent = hasData ? `${label}\n${JSON.stringify(data, null, 2)}` : label;
  entry.className = "mb-3";

  outputElement.appendChild(entry);
  outputElement.scrollTop = outputElement.scrollHeight;

  if (hasData) {
    console.log(label, data);
  } else {
    console.log(label);
  }
}

function runFilterClaims(): void {
  clearConsole();

  const filters: FilterFields = {
    locationId: selectById("filterLocation").value || undefined,
    payerName: selectById("filterPayer").value || undefined,
    status: (selectById("filterStatus").value || undefined) as Claim["status"] | undefined,
    serviceType: (selectById("filterServiceType").value || undefined) as ServiceType | undefined,
  };

  appendToConsole("filterClaims( )", filterClaims(sampleClaims, filters));
}

function runGroupClaims(): void {
  clearConsole();
  appendToConsole("groupClaimsBy(locationId)", groupClaimsBy(sampleClaims, "locationId"));
}

function runSearchClinician(): void {
  clearConsole();
  const clinicianId = selectById("clinicianIdSelect").value;
  appendToConsole(`findClinicianById(${clinicianId})`, findClinicianById(sampleClinicians, clinicianId));
}

function runDenialByPayer(): void {
  clearConsole();
  const payerName = selectById("payerSelect").value;
  const rates = denialRateByPayer(sampleClaims);

  appendToConsole("denialRateByPayer()", {
    payerName,
    denialRate: rates[payerName] || 0,
  });
}

function runDenialByLocation(): void {
  clearConsole();
  const locationId = selectById("locationSelect").value;
  const rates = denialRateByLocation(sampleClaims);

  appendToConsole(`denialRateByLocation(${locationId})`, {
    locationId,
    denialRate: rates[locationId] || 0,
  });
}

function runNoShowEstimator(): void {
  clearConsole();

  const locationId = selectById("noShowLocation").value;
  const weekEndingDate = selectById("weekEndingDate").value;
  const threshold = Number(inputById("noShowThreshold").value || "20");
  const location = sampleLocations.find((item) => item.locationId === locationId);

  if (!location) {
    appendToConsole("No-show estimator", { error: "Unknown location selected." });
    return;
  }

  const rates = noShowRateByLocation(sampleAppointments);
  const rate = rates[locationId] || 0;
  const cost = calculateNoShowCost(sampleAppointments, location, weekEndingDate);

  appendToConsole(`No-show estimator(locationId=${locationId})`, {
    locationId,
    weekEndingDate,
    noShowCostUsd: cost,
    noShowRate: rate,
    threshold,
    exceedsThreshold: rate > threshold,
  });
}

function runCMEStatus(): void {
  clearConsole();

  const status = selectById("complianceStatus").value as CMEStatus;
  const asOfDate = inputById("asOfDate").value;
  const filtered = generateCMEReport(sampleClinicians, asOfDate).filter(
    (report) => report.complianceStatus === status
  );

  appendToConsole(`CME compliance(status=${status})`, {
    status,
    asOfDate,
    clinicians: filtered,
  });
}

declare global {
  interface Window {
    clearConsole: () => void;
    runFilterClaims: () => void;
    runGroupClaims: () => void;
    runSearchClinician: () => void;
    runDenialByPayer: () => void;
    runDenialByLocation: () => void;
    runNoShowEstimator: () => void;
    runCMEStatus: () => void;
  }
}

window.clearConsole = clearConsole;
window.runFilterClaims = runFilterClaims;
window.runGroupClaims = runGroupClaims;
window.runSearchClinician = runSearchClinician;
window.runDenialByPayer = runDenialByPayer;
window.runDenialByLocation = runDenialByLocation;
window.runNoShowEstimator = runNoShowEstimator;
window.runCMEStatus = runCMEStatus;

initializeDropdowns();