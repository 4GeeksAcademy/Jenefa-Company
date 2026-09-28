/**
 * Phase 3: centralized authentication instrumentation. Call from auth hooks
 * or route middleware only — never from individual page files.
 *
 * Reported as `system_health_checked` (no dedicated auth event_type exists in
 * event-schemas.json); the exact failure token is embedded in
 * `target_subsystem` so security monitoring can still grep for it.
 */

import { track } from "./telemetry";

export type AuthFailureReason = "invalid_credentials" | "session_expired" | "network_error";

export function trackAuthFailure(reason: AuthFailureReason, durationMs = 0): void {
  track("system_health_checked", {
    target_subsystem: `auth:${reason}`,
    status_state: reason === "network_error" ? "unreachable" : "degraded",
    latency_ms: Math.max(0, Math.round(durationMs)),
  });
}

export function trackSessionExpired(): void {
  trackAuthFailure("session_expired");
}
