import {
  clearAuthToken,
  getAuthDisplayName,
  getAuthToken,
  setAuthDisplayName,
  setAuthToken,
} from "@/lib/authStorage";

describe("authStorage", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("stores and reads the clinic session token (happy path)", () => {
    setAuthToken("jwt-example-token");
    expect(getAuthToken()).toBe("jwt-example-token");
  });

  it("stores and reads the signed-in display name", () => {
    setAuthDisplayName("Dr. Marcus Reid");
    expect(getAuthDisplayName()).toBe("Dr. Marcus Reid");
  });

  it("clears the token so subsequent reads return null (failure / logout path)", () => {
    setAuthToken("jwt-example-token");
    setAuthDisplayName("Dr. Marcus Reid");
    clearAuthToken();
    expect(getAuthToken()).toBeNull();
    expect(getAuthDisplayName()).toBeNull();
  });

  it("returns null when window is unavailable (SSR edge)", () => {
    const originalWindow = globalThis.window;
    // Simulate server render: token helpers must not throw or invent a session.
    // @ts-expect-error intentional SSR simulation
    delete globalThis.window;
    expect(getAuthToken()).toBeNull();
    globalThis.window = originalWindow;
  });
});
