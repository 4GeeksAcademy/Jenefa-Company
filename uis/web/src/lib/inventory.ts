import { apiFetch, readJson } from "@/lib/api";

export type MedicalSupplySummary = {
  id: number;
  name: string;
  sku: string;
  clinic_id: string;
  regulatory_tier: string;
};

export type PartitionStock = {
  clinic_id: string;
  inbound_total: number;
  outbound_total: number;
  current_stock: number;
};

export type MedicalSupplyRead = MedicalSupplySummary & {
  current_stock: number;
};

export type MedicalSupplyDetail = MedicalSupplyRead & {
  partitions: PartitionStock[];
};

export type LedgerCreate = {
  medical_supply_id: number;
  quantity: number;
  clinic_id: string;
};

export type MedicalSupplyCreate = {
  name: string;
  sku: string;
  clinic_id: string;
  regulatory_tier: string;
};

export type OrderRead = {
  id: number;
  kind: "inbound" | "outbound";
  medical_supply_id: number;
  quantity: number;
  clinic_id: string;
  created_at: string;
  user_uuid: string;
  medical_supply: MedicalSupplySummary;
};

export async function fetchProducts(): Promise<MedicalSupplyRead[]> {
  const response = await apiFetch("/inventory/products");
  return readJson<MedicalSupplyRead[]>(response);
}

export async function createProduct(
  payload: MedicalSupplyCreate
): Promise<MedicalSupplyRead> {
  const response = await apiFetch("/inventory/products", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return readJson<MedicalSupplyRead>(response);
}

export async function fetchProduct(id: number): Promise<MedicalSupplyDetail> {
  const response = await apiFetch(`/inventory/products/${id}`);
  return readJson<MedicalSupplyDetail>(response);
}

export async function recordInbound(payload: LedgerCreate): Promise<OrderRead> {
  const response = await apiFetch("/inventory/orders/inbound", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return readJson<OrderRead>(response);
}

export async function recordOutbound(payload: LedgerCreate): Promise<OrderRead> {
  const response = await apiFetch("/inventory/orders/outbound", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return readJson<OrderRead>(response);
}

export async function fetchOrders(): Promise<OrderRead[]> {
  const response = await apiFetch("/inventory/orders");
  return readJson<OrderRead[]>(response);
}
