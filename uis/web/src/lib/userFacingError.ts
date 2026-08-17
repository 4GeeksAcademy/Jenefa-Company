export const SUPPORT_EMAIL = "access@healthcore.com";
export const SUPPORT_PHONE = "+1-800-442-5844";

export const USER_MESSAGES = {
  connection:
    "We're experiencing temporary connection issues. Your data hasn't been lost.",
  parse: "We couldn't read the server response. Please try again.",
  server: "Something went wrong on our side. Please try again in a moment.",
  unauthorized: "Your session has expired. Please sign in again.",
  forbidden: "You don't have permission to complete this action.",
  notFound: "We couldn't find what you requested.",
  generic: "We couldn't complete that request. Please try again.",
} as const;

const ERROR_NUMBER_SUFFIX = /\s*\(Error \d+\)\s*$/i;

export function withErrorNumber(message: string, code: number): string {
  const base = message.replace(ERROR_NUMBER_SUFFIX, "").trim();
  return `${base} (Error ${code})`;
}

function isTechnical(message: string): boolean {
  const lowered = message.replace(ERROR_NUMBER_SUFFIX, "").trim().toLowerCase();
  return (
    /error \d{3}/.test(lowered) ||
    /status \d{3}/.test(lowered) ||
    lowered.includes("unexpected token") ||
    lowered.includes("failed to fetch") ||
    lowered.includes("networkerror") ||
    lowered.includes("load failed") ||
    lowered.includes("econnrefused") ||
    lowered.includes("traceback") ||
    lowered.includes("internal server error") ||
    (lowered.includes("json") && lowered.includes("parse"))
  );
}

export function messageForStatus(status: number): string {
  let base: string = USER_MESSAGES.generic;
  if (status === 0) base = USER_MESSAGES.connection;
  else if (status === 401) base = USER_MESSAGES.unauthorized;
  else if (status === 403) base = USER_MESSAGES.forbidden;
  else if (status === 404) base = USER_MESSAGES.notFound;
  else if (status >= 500) base = USER_MESSAGES.server;
  return withErrorNumber(base, status);
}

function isApiRequestError(
  err: unknown
): err is Error & { status: number } {
  return (
    err instanceof Error &&
    err.name === "ApiRequestError" &&
    "status" in err &&
    typeof (err as { status: unknown }).status === "number"
  );
}

export function toUserFacingMessage(err: unknown): string {
  if (isApiRequestError(err)) {
    if (err.status === 0 || isTechnical(err.message)) {
      return messageForStatus(err.status);
    }
    if (err.status >= 500) return messageForStatus(err.status);
    return withErrorNumber(err.message || USER_MESSAGES.generic, err.status);
  }
  if (err instanceof TypeError) return withErrorNumber(USER_MESSAGES.connection, 0);
  if (err instanceof SyntaxError) return withErrorNumber(USER_MESSAGES.parse, 422);
  if (err instanceof Error) {
    if (isTechnical(err.message)) return withErrorNumber(USER_MESSAGES.generic, 500);
    return withErrorNumber(err.message || USER_MESSAGES.generic, 500);
  }
  return withErrorNumber(USER_MESSAGES.generic, 500);
}
