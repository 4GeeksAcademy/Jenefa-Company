const TOKEN_KEY = "hc_auth_token";
const DISPLAY_NAME_KEY = "hc_auth_display_name";

export function getAuthToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function getAuthDisplayName(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(DISPLAY_NAME_KEY);
}

export function setAuthDisplayName(name: string): void {
  window.localStorage.setItem(DISPLAY_NAME_KEY, name);
}

export function clearAuthToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(DISPLAY_NAME_KEY);
}

export function logoutAndRedirect(): void {
  clearAuthToken();
  window.location.replace("/login");
}
