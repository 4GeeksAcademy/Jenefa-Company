/**
 * Client-side mirror of docs/telemetry/event-schemas.json (HealthCoreTelemetryEnvelope).
 * This is the ground-truth allowlist: event_type is a closed enum, and each
 * type's `properties` map may only contain its documented keys (no padding).
 */

export type EventType =
  | "appointment_booked"
  | "appointment_noshow_predicted"
  | "billing_claim_compiled"
  | "revenue_stream_reconciled"
  | "patient_data_accessed"
  | "system_health_checked"
  | "clinical_documentation_abandoned"
  | "client_navigation_tracked";

interface PropertySchema {
  required: readonly string[];
  allowed: readonly string[];
}

export const EVENT_PROPERTY_SCHEMAS: Record<EventType, PropertySchema> = {
  appointment_booked: {
    required: ["location_id", "region", "booking_channel", "specialty_requested"],
    allowed: ["location_id", "region", "booking_channel", "specialty_requested"],
  },
  appointment_noshow_predicted: {
    required: ["location_id", "calculated_risk_score", "lead_time_days"],
    allowed: ["location_id", "calculated_risk_score", "lead_time_days", "risk_factors"],
  },
  billing_claim_compiled: {
    required: ["claim_id", "region", "payer_type", "coding_standard", "pre_check_denial_risk"],
    allowed: ["claim_id", "region", "payer_type", "coding_standard", "pre_check_denial_risk"],
  },
  revenue_stream_reconciled: {
    required: ["reconciliation_id", "currency", "gross_amount", "net_settled_amount"],
    allowed: ["reconciliation_id", "currency", "gross_amount", "net_settled_amount"],
  },
  patient_data_accessed: {
    required: ["ehr_source", "accessing_role", "jurisdiction", "anonymized_patient_token"],
    allowed: ["ehr_source", "accessing_role", "jurisdiction", "anonymized_patient_token"],
  },
  system_health_checked: {
    required: ["target_subsystem", "status_state", "latency_ms"],
    allowed: ["target_subsystem", "status_state", "latency_ms"],
  },
  clinical_documentation_abandoned: {
    required: ["screen_view_id", "time_spent_seconds", "character_count"],
    allowed: ["screen_view_id", "time_spent_seconds", "character_count"],
  },
  client_navigation_tracked: {
    required: ["origin_route", "destination_route", "user_type"],
    allowed: ["origin_route", "destination_route", "user_type"],
  },
};

export function isKnownEventType(eventType: string): eventType is EventType {
  return Object.prototype.hasOwnProperty.call(EVENT_PROPERTY_SCHEMAS, eventType);
}

/** Returns allowlist violations for a properties map; empty array means compliant. */
export function validateEventProperties(
  eventType: EventType,
  properties: Record<string, unknown>,
): string[] {
  const schema = EVENT_PROPERTY_SCHEMAS[eventType];
  const errors: string[] = [];

  for (const requiredKey of schema.required) {
    if (!(requiredKey in properties)) {
      errors.push(`Missing required property "${requiredKey}" for event_type "${eventType}"`);
    }
  }

  for (const key of Object.keys(properties)) {
    if (!schema.allowed.includes(key)) {
      errors.push(`Property "${key}" is not allowlisted for event_type "${eventType}"`);
    }
  }

  return errors;
}
