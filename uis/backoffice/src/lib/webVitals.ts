/**
 * Phase 3: Web Vitals instrumentation. No dedicated event_type exists for
 * vitals in event-schemas.json, so each metric is reported as
 * `system_health_checked` with the metric name and route folded into
 * `target_subsystem` per the spec's "route context in properties" rule.
 */

import { track } from "../services/telemetry";

interface WebVitalMetric {
  name: string;
  value: number;
  navigationType?: string;
}

const GOOD_THRESHOLDS: Record<string, number> = {
  LCP: 2_500,
  FID: 100,
  CLS: 0.1,
  TTFB: 600,
};

const POOR_THRESHOLDS: Record<string, number> = {
  LCP: 4_000,
  FID: 300,
  CLS: 0.25,
  TTFB: 1_800,
};

function ratingFor(name: string, value: number): "healthy" | "degraded" | "unreachable" {
  const poor = POOR_THRESHOLDS[name];
  const good = GOOD_THRESHOLDS[name];
  if (poor !== undefined && value > poor) return "unreachable";
  if (good !== undefined && value > good) return "degraded";
  return "healthy";
}

/** Wire this into Next.js `reportWebVitals` (or a framework-agnostic equivalent). */
export function handleWebVital(metric: WebVitalMetric): void {
  const route = typeof window !== "undefined" ? window.location.pathname : "unknown";
  // CLS is a unitless score (typically < 1); scale to ms-equivalent for the latency_ms field.
  const latencyMs = metric.name === "CLS" ? metric.value * 1000 : metric.value;

  track("system_health_checked", {
    target_subsystem: `web_vitals:${metric.name}:${route}`,
    status_state: ratingFor(metric.name, metric.value),
    latency_ms: Math.round(latencyMs),
  });
}
