export const SUPPORT_EMAIL = "access@healthcore.com";
export const SUPPORT_PHONE = "+1-800-442-5844";

export const USER_MESSAGES = {
  connection:
    "We're experiencing temporary connection issues. Your data hasn't been lost.",
  parse: "We couldn't read the server response. Please try again.",
  server: "Something went wrong on our side. Please try again in a moment.",
  forbidden: "You don't have permission to complete this action.",
  notFound: "We couldn't find what you requested.",
  generic: "We couldn't complete that request. Please try again.",
} as const;

function isTechnical(message: string): boolean {
  const lowered = message.toLowerCase();
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
    (lowered.includes("json") && lowered.includes("parse")) ||
    lowered.includes("request failed with status")
  );
}

export function messageForStatus(status: number): string {
  if (status === 0) return USER_MESSAGES.connection;
  if (status === 403) return USER_MESSAGES.forbidden;
  if (status === 404) return USER_MESSAGES.notFound;
  if (status >= 500) return USER_MESSAGES.server;
  return USER_MESSAGES.generic;
}

function isApiRequestError(err: unknown): err is Error & { status: number } {
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
    if (err.status >= 500) return USER_MESSAGES.server;
    return err.message || messageForStatus(err.status);
  }
  if (err instanceof TypeError) return USER_MESSAGES.connection;
  if (err instanceof SyntaxError) return USER_MESSAGES.parse;
  if (err instanceof Error) {
    if (isTechnical(err.message)) return USER_MESSAGES.generic;
    return err.message || USER_MESSAGES.generic;
  }
  return USER_MESSAGES.generic;
}
