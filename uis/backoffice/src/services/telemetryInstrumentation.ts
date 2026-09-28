/**
 * Phase 3: cross-cutting technical instrumentation baseline.
 *
 * event-schemas.json has no generic "error" event_type, so uncaught errors
 * and slow network calls are reported as `system_health_checked` with the
 * failure context folded into `target_subsystem` (the only free-text slot),
 * keeping every payload key on the documented allowlist.
 */

import { Component, ErrorInfo, ReactNode } from "react";
import { track } from "./telemetry";

const SLOW_CALL_THRESHOLD_MS = 1_000; // matches telemetry-plan.md throttling ceiling

function reportHealth(targetSubsystem: string, statusState: "healthy" | "degraded" | "unreachable", latencyMs: number): void {
  track("system_health_checked", {
    target_subsystem: targetSubsystem,
    status_state: statusState,
    latency_ms: Math.max(0, Math.round(latencyMs)),
  });
}

/** Binds `window.onerror` and `unhandledrejection` to telemetry. Call once at app startup. */
export function initErrorTracking(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.addEventListener("error", (event: ErrorEvent) => {
    reportHealth(`backoffice_client:${event.error?.name ?? "Error"}`, "degraded", 0);
  });

  window.addEventListener("unhandledrejection", (event: PromiseRejectionEvent) => {
    const name = event.reason instanceof Error ? event.reason.name : "UnhandledRejection";
    reportHealth(`backoffice_client:${name}`, "degraded", 0);
  });
}

/** Wraps `window.fetch` to report slow or failed API calls (e.g. EHR sync wrappers). */
export function initFetchLatencyTracking(): void {
  if (typeof window === "undefined" || (window.fetch as { __telemetryWrapped?: boolean }).__telemetryWrapped) {
    return;
  }

  const originalFetch = window.fetch.bind(window);

  const wrapped = async (...args: Parameters<typeof fetch>): Promise<Response> => {
    const url = args[0] instanceof Request ? args[0].url : String(args[0]);
    const start = performance.now();
    try {
      const response = await originalFetch(...args);
      const durationMs = performance.now() - start;
      if (!response.ok) {
        reportHealth(`api_call:${url}`, "degraded", durationMs);
      } else if (durationMs > SLOW_CALL_THRESHOLD_MS) {
        reportHealth(`api_call:${url}`, "degraded", durationMs);
      }
      return response;
    } catch (error) {
      reportHealth(`api_call:${url}`, "unreachable", performance.now() - start);
      throw error;
    }
  };
  (wrapped as { __telemetryWrapped?: boolean }).__telemetryWrapped = true;
  window.fetch = wrapped as typeof fetch;
}

/** Reports page load duration once per navigation. */
export function trackPageLoadPerformance(): void {
  if (typeof window === "undefined") {
    return;
  }
  window.addEventListener("load", () => {
    const [entry] = performance.getEntriesByType("navigation") as PerformanceNavigationTiming[];
    if (entry) {
      reportHealth(`page_load:${window.location.pathname}`, "healthy", entry.loadEventEnd - entry.startTime);
    }
  });
}

/** Call from router navigation events (no dedicated router is wired up yet). */
export function trackNavigation(
  originRoute: string,
  destinationRoute: string,
  userType: "patient" | "clinical_staff" | "operations_staff",
): void {
  track("client_navigation_tracked", {
    origin_route: originRoute,
    destination_route: destinationRoute,
    user_type: userType,
  });
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

/** Root interface error boundary; reports caught render errors via `system_health_checked`. */
export class TelemetryErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, _info: ErrorInfo): void {
    reportHealth(`backoffice_client:boundary:${error.name}`, "degraded", 0);
  }

  render(): ReactNode {
    return this.state.hasError ? this.props.fallback : this.props.children;
  }
}
