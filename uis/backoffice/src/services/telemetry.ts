/**
 * Centralized TelemetryService (Phase 2) for HealthCore backoffice.
 *
 * `track()` is the ONLY sanctioned entry point for telemetry — consumer code
 * must never call fetch/axios against the telemetry endpoint directly, and
 * must never pass eventId/sessionId/userId/timestamp/schemaVersion/requestId
 * (this module auto-populates them at capture time).
 */

import { EventType, isKnownEventType, validateEventProperties } from "../lib/telemetrySchemas";

interface TelemetryEnvelope {
  eventId: string;
  timestamp: string;
  sessionId: string;
  userId: string | null;
  event_type: EventType;
  schemaVersion: string;
  requestId: string;
  properties: Record<string, unknown>;
}

interface TelemetryBatchRequest {
  events: TelemetryEnvelope[];
}

const SCHEMA_VERSION = "1.0.0";
const BATCH_INTERVAL_MS = 10_000;
const BATCH_SIZE_THRESHOLD = 20;
const MAX_RETRY_ATTEMPTS = 3;
const INITIAL_BACKOFF_MS = 1_000;

const SESSION_STORAGE_KEY = "hc_telemetry_session_id";
const AUTH_TOKEN_KEY = "hc_auth_token";

let queue: TelemetryEnvelope[] = [];
let flushTimer: ReturnType<typeof setInterval> | null = null;
let cachedSessionId: string | null = null;

function resolveTelemetryEndpoint(): string {
  return process.env.NEXT_PUBLIC_TELEMETRY_ENDPOINT || "http://localhost:8000/telemetry/events";
}

function getOrCreateSessionId(): string {
  if (typeof window === "undefined") {
    return "server";
  }
  if (cachedSessionId) {
    return cachedSessionId;
  }
  let sessionId = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  }
  cachedSessionId = sessionId;
  return sessionId;
}

/** Decodes the `sub` claim from the stored JWT without verifying the signature. */
function getUserId(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  const token = window.localStorage.getItem(AUTH_TOKEN_KEY);
  if (!token) {
    return null;
  }
  try {
    const payloadSegment = token.split(".")[1];
    const payload = JSON.parse(atob(payloadSegment.replace(/-/g, "+").replace(/_/g, "/")));
    return typeof payload.sub === "string" ? payload.sub : null;
  } catch {
    return null;
  }
}

/**
 * Track a telemetry event. Non-blocking: validation failures are dropped
 * with a console warning rather than throwing, per "never block workflows".
 */
export function track(eventType: string, properties: Record<string, unknown> = {}): void {
  if (!isKnownEventType(eventType)) {
    console.warn(`[telemetry] unknown event_type "${eventType}"; dropped`);
    return;
  }

  const violations = validateEventProperties(eventType, properties);
  if (violations.length > 0) {
    console.warn(`[telemetry] schema violations for "${eventType}":`, violations);
    return;
  }

  const envelope: TelemetryEnvelope = {
    eventId: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    sessionId: getOrCreateSessionId(),
    userId: getUserId(),
    event_type: eventType,
    schemaVersion: SCHEMA_VERSION,
    requestId: crypto.randomUUID(),
    properties,
  };

  queue.push(envelope);

  if (queue.length >= BATCH_SIZE_THRESHOLD) {
    void flush();
  }
}

/** Starts the 10-second periodic flush loop and tab-close flushing hooks. */
export function initTelemetry(): void {
  if (typeof window === "undefined") {
    return;
  }

  if (flushTimer === null) {
    flushTimer = setInterval(() => {
      if (queue.length > 0) {
        void flush();
      }
    }, BATCH_INTERVAL_MS);
  }

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      flushViaBeacon();
    }
  });
  window.addEventListener("pagehide", flushViaBeacon);
}

export function shutdownTelemetry(): void {
  if (flushTimer !== null) {
    clearInterval(flushTimer);
    flushTimer = null;
  }
  flushViaBeacon();
}

async function flush(): Promise<void> {
  if (queue.length === 0) {
    return;
  }
  const batch = queue;
  queue = [];

  const endpoint = resolveTelemetryEndpoint();
  const body = JSON.stringify({ events: batch } satisfies TelemetryBatchRequest);

  for (let attempt = 1; attempt <= MAX_RETRY_ATTEMPTS; attempt += 1) {
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return;
    } catch (error) {
      if (attempt === MAX_RETRY_ATTEMPTS) {
        console.warn("[telemetry] batch dropped after max retry attempts", error);
        return;
      }
      const backoffMs = INITIAL_BACKOFF_MS * 2 ** (attempt - 1);
      await new Promise((resolve) => setTimeout(resolve, backoffMs));
    }
  }
}

function flushViaBeacon(): void {
  if (queue.length === 0 || typeof navigator === "undefined" || !navigator.sendBeacon) {
    return;
  }
  const batch = queue;
  queue = [];
  const body = JSON.stringify({ events: batch } satisfies TelemetryBatchRequest);
  navigator.sendBeacon(resolveTelemetryEndpoint(), body);
}
