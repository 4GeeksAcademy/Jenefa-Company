interface ExecutiveKpi {
  reporting_window_timestamp: string;
  clinic_location_id: string;
  market_region: string;
  network_appointment_volume: number | null;
  global_no_show_rate: number | null;
  claims_denial_rate: number | null;
  revenue_currency: string | null;
  revenue_net_settled: number | null;
}

// Reporting is served from the live API and must be resolved at request time.
// Keeping this explicit also prevents a production build from treating the
// page as a missing/static route when the API is unavailable during build.
export const dynamic = "force-dynamic";

function percent(value: number | null): string {
  return value === null ? "—" : `${(value * 100).toFixed(1)}%`;
}

async function fetchExecutiveKpis(): Promise<ExecutiveKpi[]> {
  const backend = process.env.HC_API_INTERNAL_URL || "http://localhost:8000";
  const response = await fetch(`${backend.replace(/\/$/, "")}/services/reporting/kpis`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Reporting API returned HTTP ${response.status}`);
  }

  return response.json() as Promise<ExecutiveKpi[]>;
}

export default async function ReportingPage() {
  let rows: ExecutiveKpi[] = [];
  let error = "";

  try {
    rows = await fetchExecutiveKpis();
  } catch (cause) {
    error = cause instanceof Error ? cause.message : "Unable to load reporting data";
  }

  const period = rows[0]?.reporting_window_timestamp
    ? new Date(rows[0].reporting_window_timestamp).toLocaleDateString()
    : "No completed weekly run";

  return (
    <main style={{ maxWidth: 1100, margin: "2rem auto", fontFamily: "sans-serif", padding: "0 1rem" }}>
      <h1>HealthCore Executive Reporting</h1>
      <p>Weekly reporting period ending: <strong>{period}</strong></p>
      {error && <p role="alert">Reporting data unavailable: {error}</p>}
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            {["Clinic", "Region", "Network appointment volume", "Global no-show rate", "Claims denial rate", "Revenue net settled"].map((heading) => (
              <th key={heading} style={{ textAlign: "left", borderBottom: "2px solid #333", padding: ".6rem" }}>{heading}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${row.reporting_window_timestamp}-${row.clinic_location_id}`}>
              <td style={{ padding: ".6rem" }}>{row.clinic_location_id}</td>
              <td style={{ padding: ".6rem" }}>{row.market_region}</td>
              <td style={{ padding: ".6rem" }}>{row.network_appointment_volume ?? "—"}</td>
              <td style={{ padding: ".6rem" }}>{percent(row.global_no_show_rate)}</td>
              <td style={{ padding: ".6rem" }}>{percent(row.claims_denial_rate)}</td>
              <td style={{ padding: ".6rem" }}>{row.revenue_net_settled === null ? "—" : `${row.revenue_currency ?? ""} ${row.revenue_net_settled.toFixed(2)}`}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
