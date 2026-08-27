import { ApiRequestError, readJson } from "@/lib/api";

function mockResponse(body: string, status: number): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: async () => body,
  } as Response;
}

describe("api.readJson", () => {
  it("returns parsed JSON on a successful auth response (happy path)", async () => {
    const payload = { access_token: "abc.def.ghi", token_type: "bearer" };
    const result = await readJson(mockResponse(JSON.stringify(payload), 200));
    expect(result).toEqual(payload);
  });

  it("raises ApiRequestError with business detail on failure (failure mode)", async () => {
    const body = JSON.stringify({ detail: "Incorrect email or password" });
    await expect(readJson(mockResponse(body, 401))).rejects.toMatchObject({
      name: "ApiRequestError",
      status: 401,
      message: "Incorrect email or password",
    } satisfies Partial<ApiRequestError>);
  });

  it("rejects invalid JSON bodies without leaking parse internals", async () => {
    await expect(readJson(mockResponse("{not-json", 200))).rejects.toBeInstanceOf(
      ApiRequestError
    );
  });
});
