import type { ApiError } from "@/types";
import { USER_MESSAGES, messageForStatus } from "@/lib/userFacingError";

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
  return messageForStatus(response.status);
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });
  } catch {
    throw new ApiRequestError(USER_MESSAGES.connection, 0);
  }

  if (!response.ok) {
    const message = await parseErrorResponse(response);
    throw new ApiRequestError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiRequestError(USER_MESSAGES.parse, response.status);
  }
}
