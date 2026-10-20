import { forwardedPortUrl } from "@/lib/forwardedPort";

export type ExecutiveKpi = {
  reporting_window_timestamp: string;
  clinic_location_id: string;
  market_region: string;
  network_appointment_volume: number | null;
  global_no_show_rate: number | null;
  claims_denial_rate: number | null;
  revenue_currency: string | null;
  revenue_net_settled: number | null;
  patient_satisfaction_score: number | null;
};

// Empty env values must fall back, so use || rather than ??
function getReportingEndpoint(): string {
  return process.env.NEXT_PUBLIC_REPORTING_ENDPOINT || `${forwardedPortUrl(8000)}/services/reporting`;
}

export async function fetchExecutiveKpis(): Promise<ExecutiveKpi[]> {
  const response = await fetch(`${getReportingEndpoint()}/kpis`, { cache: "no-store" });
  if (!response.ok) throw new Error(`Reporting API returned HTTP ${response.status}`);
  return response.json() as Promise<ExecutiveKpi[]>;
}


export function flowerMonitorUrl(): string {
  return process.env.NEXT_PUBLIC_FLOWER_URL || forwardedPortUrl(5555);
}

export function summarizeExecutiveKpis(rows: ExecutiveKpi[]) {
  const average = (values: Array<number | null>) => {
    const present = values.filter((value): value is number => value !== null);
    return present.length ? present.reduce((total, value) => total + value, 0) / present.length : null;
  };
  return {
    period: rows[0]?.reporting_window_timestamp ?? null,
    totalAppointments: rows.reduce((total, row) => total + (row.network_appointment_volume ?? 0), 0),
    averageNoShow: average(rows.map((row) => row.global_no_show_rate)),
    averageDenial: average(rows.map((row) => row.claims_denial_rate)),
  };
}
