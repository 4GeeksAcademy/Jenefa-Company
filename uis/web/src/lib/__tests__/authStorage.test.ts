import { clearAuthToken, getAuthToken, setAuthToken } from "@/lib/authStorage";

describe("authStorage", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("stores and reads the clinic session token (happy path)", () => {
    setAuthToken("jwt-example-token");
    expect(getAuthToken()).toBe("jwt-example-token");
  });

  it("clears the token so subsequent reads return null (failure / logout path)", () => {
    setAuthToken("jwt-example-token");
    clearAuthToken();
    expect(getAuthToken()).toBeNull();
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
