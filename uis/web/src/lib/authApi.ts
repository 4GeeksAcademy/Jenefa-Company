import { apiFetch, readJson } from "@/lib/api";
import { setAuthToken } from "@/lib/authStorage";

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
}

export async function loginAndStore(email: string, password: string): Promise<void> {
  const token = await login(email, password);
  setAuthToken(token.access_token);
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
