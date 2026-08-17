import { getAuthToken, logoutAndRedirect } from "@/lib/authStorage";
import { USER_MESSAGES, messageForStatus } from "@/lib/userFacingError";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  process.env.NEXT_PUBLIC_INCIDENT_API_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

export type FieldError = {
  field: string;
  message: string;
};

export class ApiRequestError extends Error {
  status: number;
  fieldErrors: FieldError[];

  constructor(message: string, status: number, fieldErrors: FieldError[] = []) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

type FastApiErrorItem = {
  loc?: Array<string | number>;
  msg?: string;
};

function parseDetail(detail: unknown): { message: string; fieldErrors: FieldError[] } {
  if (typeof detail === "string") {
    return { message: detail, fieldErrors: [] };
  }
  if (Array.isArray(detail)) {
    const fieldErrors: FieldError[] = detail.map((item: FastApiErrorItem) => {
      const loc = item.loc ?? [];
      const field = loc.filter((part) => part !== "body").join(".") || "form";
      return { field, message: item.msg ?? "Invalid value" };
    });
    const message =
      fieldErrors.map((error) => `${error.field}: ${error.message}`).join(" ") ||
      "Validation failed.";
    return { message, fieldErrors };
  }
  return { message: "Request failed.", fieldErrors: [] };
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const token = getAuthToken();
  const headers = new Headers(init.headers);

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const isFormData = typeof FormData !== "undefined" && init.body instanceof FormData;
  if (init.body && !isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  } catch {
    throw new ApiRequestError(USER_MESSAGES.connection, 0);
  }

  const method = (init.method ?? "GET").toUpperCase();
  const isPublicAuthCall =
    path === "/auth/login" ||
    path === "/auth/forgot-password" ||
    path === "/auth/reset-password" ||
    (path === "/users" && method === "POST");
  if (response.status === 401 && token && !isPublicAuthCall) {
    logoutAndRedirect();
  }

  return response;
}

export async function readJson<T>(response: Response): Promise<T> {
  let text: string;
  try {
    text = await response.text();
  } catch {
    throw new ApiRequestError(USER_MESSAGES.connection, response.status || 0);
  }

  let payload: { detail?: unknown; error?: string } = {};
  if (text) {
    try {
      payload = JSON.parse(text) as { detail?: unknown; error?: string };
    } catch {
      throw new ApiRequestError(
        response.ok ? USER_MESSAGES.parse : messageForStatus(response.status),
        response.status
      );
    }
  }

  if (!response.ok) {
    const parsed = parseDetail(payload.detail);
    const fallback =
      typeof payload.error === "string" ? payload.error : messageForStatus(response.status);
    throw new ApiRequestError(parsed.message || fallback, response.status, parsed.fieldErrors);
  }
  return payload as T;
}
