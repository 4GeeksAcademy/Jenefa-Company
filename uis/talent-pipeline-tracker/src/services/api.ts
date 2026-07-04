import type { ApiError } from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "https://playground.4geeks.com/tracker/api/v1";

export class ApiRequestError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
  }
}

async function parseErrorResponse(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as ApiError;
    if (body.detail?.length) {
      return body.detail.map((item) => item.msg).join(". ");
    }
    if (body.message) {
      return body.message;
    }
  } catch {
    // fall through to generic message
  }
  return `Request failed with status ${response.status}`;
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const message = await parseErrorResponse(response);
    throw new ApiRequestError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
