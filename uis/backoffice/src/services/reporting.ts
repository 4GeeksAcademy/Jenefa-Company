export interface ExecutiveKpi {
  reporting_window_timestamp: string;
  clinic_location_id: string;
  market_region: string;
  network_appointment_volume: number | null;
  global_no_show_rate: number | null;
  claims_denial_rate: number | null;
  revenue_currency: string | null;
  revenue_net_settled: number | null;
  patient_satisfaction_score: number | null;
}

const endpoint = process.env.NEXT_PUBLIC_REPORTING_ENDPOINT || "http://localhost:8000/services/reporting";

export async function fetchExecutiveKpis(): Promise<ExecutiveKpi[]> {
  const response = await fetch(`${endpoint}/kpis`, { cache: "no-store" });
  if (!response.ok) throw new Error(`Reporting API returned HTTP ${response.status}`);
  return response.json() as Promise<ExecutiveKpi[]>;
}
