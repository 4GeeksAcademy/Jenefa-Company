const API_BASE =
  process.env.NEXT_PUBLIC_SUPPLIER_API_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

export const SUPPLIER_CATEGORIES = [
  "medical_supplies",
  "laboratory_services",
  "pharmaceutical",
  "clinical_software",
  "it_infrastructure",
  "hr_and_payroll_software",
  "cleaning_and_facilities",
  "patient_communication",
  "billing_and_coding_software",
  "training_platforms",
] as const;

export const SUPPLIER_COUNTRIES = ["USA", "UK"] as const;

export type SupplierCountry = (typeof SUPPLIER_COUNTRIES)[number];
export type SupplierCategory = (typeof SUPPLIER_CATEGORIES)[number];
export type SupplierStatus = "active" | "suspended";
export type ComplianceAgreement = "BAA" | "DPA" | "both" | null;

export type Supplier = {
  id: number;
  name: string;
  country: SupplierCountry;
  categories: string[];
  monthly_rate: number;
  currency: "USD" | "GBP";
  status: SupplierStatus;
  compliance_agreement: ComplianceAgreement;
  contract_renewal_date?: string | null;
  contact_email?: string | null;
  notes?: string | null;
  updated_at: string;
};

export type SupplierCreateInput = {
  name: string;
  country: SupplierCountry;
  categories: string[];
  monthly_rate: number;
  currency: "USD" | "GBP";
  status: SupplierStatus;
  compliance_agreement?: ComplianceAgreement;
  contract_renewal_date?: string | null;
  contact_email?: string | null;
  notes?: string | null;
};

async function readError(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as {
      detail?: string | Array<{ msg?: string }>;
    };
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map((d) => d.msg ?? JSON.stringify(d)).join("; ");
    }
    return response.statusText || "Request failed";
  } catch {
    return response.statusText || "Request failed";
  }
}

export function currencyForCountry(country: SupplierCountry): "USD" | "GBP" {
  return country === "UK" ? "GBP" : "USD";
}

export async function listSuppliers(filters?: {
  country?: string;
  category?: string;
}): Promise<Supplier[]> {
  const params = new URLSearchParams();
  if (filters?.country) params.set("country", filters.country);
  if (filters?.category) params.set("category", filters.category);
  const qs = params.toString();
  const response = await fetch(`${API_BASE}/suppliers${qs ? `?${qs}` : ""}`);
  if (!response.ok) throw new Error(await readError(response));
  return (await response.json()) as Supplier[];
}

export async function createSupplier(
  input: SupplierCreateInput
): Promise<Supplier> {
  const response = await fetch(`${API_BASE}/suppliers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) throw new Error(await readError(response));
  return (await response.json()) as Supplier;
}

export async function updateSupplierRate(
  id: number,
  monthly_rate: number
): Promise<Supplier> {
  const response = await fetch(`${API_BASE}/suppliers/${id}/rate`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ monthly_rate }),
  });
  if (!response.ok) throw new Error(await readError(response));
  return (await response.json()) as Supplier;
}

export async function updateSupplierStatus(
  id: number,
  status: SupplierStatus
): Promise<Supplier> {
  const response = await fetch(`${API_BASE}/suppliers/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!response.ok) throw new Error(await readError(response));
  return (await response.json()) as Supplier;
}
