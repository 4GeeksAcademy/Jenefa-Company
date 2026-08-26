import { apiFetch, readJson } from "@/lib/api";
import { setAuthDisplayName, setAuthToken } from "@/lib/authStorage";

export type Profile = {
  id: string;
  user_id: string;
  name: string;
  phone: string;
  address: string;
};

export type MeResponse = {
  email: string;
  role: string;
  profile: Profile | null;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type RegisterPayload = {
  email: string;
  password: string;
  name?: string;
  phone?: string;
  address?: string;
};

function toTitleCase(words: string): string {
  return words
    .split(/\s+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
}

function deriveDisplayName(email: string, profileName?: string | null): string {
  const cleanProfile = (profileName || "").trim();
  if (cleanProfile) {
    return cleanProfile;
  }

  const localPart = email.split("@")[0] || "staff";
  const normalized = localPart.replace(/[._-]+/g, " ").trim();
  return normalized ? toTitleCase(normalized) : "Staff";
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const response = await apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  return readJson<TokenResponse>(response);
}

export async function registerUser(payload: RegisterPayload): Promise<void> {
  const response = await apiFetch("/users", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  await readJson(response);
}

export async function registerAndLogin(payload: RegisterPayload): Promise<void> {
  await registerUser(payload);
  const token = await login(payload.email, payload.password);
  setAuthToken(token.access_token);
  setAuthDisplayName(deriveDisplayName(payload.email, payload.name));
}

export async function loginAndStore(email: string, password: string): Promise<void> {
  const token = await login(email, password);
  setAuthToken(token.access_token);
  try {
    const me = await fetchMe();
    setAuthDisplayName(deriveDisplayName(me.email, me.profile?.name));
  } catch {
    // Keep sign-in resilient if profile lookup is temporarily unavailable.
    setAuthDisplayName(deriveDisplayName(email));
  }
}

export async function fetchMe(): Promise<MeResponse> {
  const response = await apiFetch("/auth/me");
  return readJson<MeResponse>(response);
}

export async function fetchMyProfile(): Promise<Profile> {
  const response = await apiFetch("/profiles/me");
  return readJson<Profile>(response);
}

export async function updateMyProfile(payload: {
  name: string;
  phone: string;
  address: string;
}): Promise<Profile> {
  const response = await apiFetch("/profiles/me", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
  return readJson<Profile>(response);
}

export type MessageResponse = {
  message: string;
};

export async function requestPasswordReset(email: string): Promise<MessageResponse> {
  const response = await apiFetch("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
  return readJson<MessageResponse>(response);
}

export async function resetPassword(
  token: string,
  newPassword: string
): Promise<MessageResponse> {
  const response = await apiFetch("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, new_password: newPassword }),
  });
  return readJson<MessageResponse>(response);
}

export async function changePassword(
  currentPassword: string,
  newPassword: string
): Promise<MessageResponse> {
  const response = await apiFetch("/auth/change-password", {
    method: "POST",
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });
  return readJson<MessageResponse>(response);
}
