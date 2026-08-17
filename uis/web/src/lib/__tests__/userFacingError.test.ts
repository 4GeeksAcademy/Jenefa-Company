import {
  messageForStatus,
  toUserFacingMessage,
  USER_MESSAGES,
} from "@/lib/userFacingError";
import { ApiRequestError } from "@/lib/api";

describe("userFacingError", () => {
  it("maps HTTP status codes to operator-safe copy (happy path)", () => {
    expect(messageForStatus(401)).toContain(USER_MESSAGES.unauthorized);
    expect(messageForStatus(401)).toMatch(/\(Error 401\)$/);
    expect(messageForStatus(403)).toContain(USER_MESSAGES.forbidden);
  });

  it("never surfaces technical connection text to operators (failure mode)", () => {
    const err = new ApiRequestError("Failed to fetch", 0);
    const message = toUserFacingMessage(err);
    expect(message).toContain(USER_MESSAGES.connection);
    expect(message.toLowerCase()).not.toContain("failed to fetch");
    expect(message.toLowerCase()).not.toContain("traceback");
  });
});
