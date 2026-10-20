# BRIEFING — HealthCore

## Telemetry Projects (Plan · Capture · Storage · Report)

<!-- hide -->

_Estas instrucciones están [disponibles en español](./healthcore-BRIEFING.es.md)._

<!-- endhide -->

---

## 1. Your Company

HealthCore operates 12 outpatient clinics across the United States (Texas, Florida, Georgia) and the United Kingdom (London, Manchester). The inventory system controls the **clinical supplies**: commonly used medications, wound-care material, PPE (personal protective equipment), and consultation-room consumables at each clinic.

Your Telemetry Plan, capture, storage, and technical report all revolve around that system. Later on, this same telemetry will feed the network operations dashboard and Dr. Okonkwo's monthly executive report.

> ⚠️ **Regulatory note (HIPAA / UK GDPR):** the events in this system describe **supplies and stock**, never patients. No `properties` field may contain patient names, medical record identifiers, diagnoses, or any real or simulated data that could be interpreted as protected health information (PHI). If you need to associate a supply consumption event with a clinical context, use only the `department` or service type (e.g. `general_consultation`, `chronic_care`), never a patient identifier.

---

## 2. Inventory System Entities at HealthCore

| Entity          | At HealthCore this means...                                                                                     |
| --------------- | ---------------------------------------------------------------------------------------------------------------- |
| `Product`      | A clinical or consultation-room supply item: e.g. `nitrile gloves (box)`, `5ml syringes`, `flu vaccine`, `surgical mask`. Each product has a category (`medication`, `ppe`, `consumable`, `equipment`) and, where applicable, an expiry date. |
| `InboundOrder`  | An inbound order: receipt of supplies from a vendor at a clinic.                                                 |
| `OutboundOrder` | An outbound order: consumption of a supply during clinical care (recorded by department, not by patient).       |
| `clinic`        | One of the 12 clinics, identified by country (`US`/`UK`) and state/region.                                       |
| `department`    | Primary care, specialty care, chronic disease management, etc.                                                   |

---

## 3. Mandatory Telemetry Metrics

These are the metrics HealthCore needs to measure **from day one**, regardless of what else you identify in your own catalogue. They go straight into the floor of your Telemetry Plan (Phase 1) and must be instrumented end-to-end by the end of the project series.

> These metrics will feed, further along in the course, Dr. Okonkwo's network operations dashboard and Claire's compliance alerts. Design them with the future in mind — they will need to be aggregated by clinic and by country (US/UK), always respecting HIPAA and UK GDPR.

| `event_type`                    | Fires when...                                                                                  | Business hypothesis                                                                                              | Decision it enables                                                                                    |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `inbound_order_created`           | A clinic registers the receipt of supplies from a vendor                                              | We need to know how much and what supply is being purchased, by clinic and vendor                                  | Consolidate purchasing across clinics and negotiate better vendor terms                                        |
| `outbound_order_created`          | A clinic registers the consumption of a supply in a department's care activity                       | We need to know which supplies are consumed most, and at what rate, by clinic and department                       | Adjust automatic replenishment of critical supplies per clinic                                                 |
| `stock_threshold_triggered`      | A supply's stock at a clinic falls below the configured minimum                                       | We need to know how often a clinic runs short of a critical supply (e.g. PPE, medication)                          | Prioritise urgent restocking and escalate to Marcus (Clinical Operations)                                      |
| `direct_stock_edit_rejected`     | A user attempts to modify stock directly (outside an order) and the system rejects it                 | We need to know if staff are attempting to bypass supply traceability controls                                     | Reinforce training or permissions at the clinic where this happens most                                        |
| `supply_expiry_flagged`         | A supply batch (medication or material) approaches its expiry date (e.g. within 30 days)              | We need to know which supplies are about to expire before they become waste or a compliance risk                    | Prioritise use or controlled disposal of that batch before expiry                                              |

**Minimum `properties` fields for inventory events** (in addition to the standard envelope): `clinic_id`, `country` (`US`/`UK`), `product_id`, `product_category` (`medication`/`ppe`/`consumable`/`equipment`), `quantity`, `department` (only where applicable, never a patient identifier).

⚠️ **Critical reminder:** no event in this catalogue may contain PHI. `department` describes the clinical area, not the person being treated.

---

## 4. How These Metrics Connect to the Future

These metrics are not just for today's technical report. As the course progresses, this same data will be reused for automation and for executive-level reporting — at a level of aggregation and polish well beyond what you're building right now. Design them as if someone else, later on, will depend on them without being able to ask you how they work.

---

## 5. Suggested Seed Data

Generate at least:

- 8–10 distinct supply items, covering all 4 categories (`medication`, `ppe`, `consumable`, `equipment`)
- 3 clinics (at least one in the US and one in the UK)
- 15–20 inbound orders distributed across those clinics
- 15–20 outbound orders, associated only with `department`, never with a patient
- At least 2 cases that trigger `stock_threshold_triggered` and 1 case of `supply_expiry_flagged`

---

## 6. Business Constraints

- Stock is never modified directly: every modification goes through `InboundOrder` or `OutboundOrder`, traceable to a staff user (never to a patient).
- No real or simulated patient data (name, medical record identifier, diagnosis) may appear in any field of these events, not even as test data.
- Supplies with an expiry date must record that date on the `Product` model, not just on the order — this is what makes `supply_expiry_flagged` computable consistently across clinics.

# BRIEFING — HealthCore (Business Performance Pipeline)

## Data Pipeline Projects (Design · Implementation · Subflows & Tests)

<!-- hide -->

_Estas instrucciones están [disponibles en español](./healthcore-pipeline-BRIEFING.es.md)._

<!-- endhide -->

This file is self-contained: it gives you everything you need to scope, build, and test the business performance pipeline for HealthCore, without having to go hunting through other documents. It builds directly on the mandatory metrics already defined in your `healthcore-BRIEFING.md` (telemetry) — read that first if you haven't.

> ⚠️ **Regulatory note (HIPAA / UK GDPR):** this pipeline aggregates supply-chain data only. As with the telemetry system, no output of this pipeline may contain patient identifiers, diagnoses, or any real or simulated PHI — everything here is aggregated by `clinic` and `department`, never by patient.

---

## 1. The business deliverable

Dr. Okonkwo (CEO) wants a **monthly board-ready pack** she can review without her team spending two days consolidating spreadsheets — comparing supply cost and stockout risk across the network's 12 clinics, US and UK.

> **Target deliverable:** a monthly, per-clinic, per-country rollup of supply cost, stockout activity, and expiry risk — the "Monthly Clinic Supply Performance Report."

This is the **one concrete deliverable** your pipeline exists to produce. Everything in your `PIPELINE_DESIGN.md` should trace back to it.

**Audience:** Dr. Okonkwo (CEO) and Claire (Chief Compliance Officer) — non-technical stakeholders who need numbers, not raw events.
**Cadence:** monthly (ready by the first working day of the month, matching the existing "automated board reporting pack" expectation leadership already has).

---

## 2. KPIs to Measure

**These are the KPIs this pipeline exists to produce.** Everything else in this document — source events, aggregation logic, table schema — is implementation detail in service of these four numbers. If you're unsure what to build next, come back to this list.

| KPI                            | What it measures                                                                                     | Why it matters to HealthCore                                                                              |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------|
| **Supply Cost per Clinic**       | How much a clinic spent purchasing medical supplies during the month.                                    | Shows where spending concentrates across the network and feeds cross-clinic purchasing decisions.              |
| **Supply Consumption Volume**    | How many supply-consumption events a clinic recorded during the month, by department.                    | The operational-activity signal — helps distinguish a genuinely busy clinic from a data-capture gap.           |
| **Critical Stockout Frequency**  | How many times during the month a clinic ran below the minimum threshold for a supply.                   | A patient-safety and compliance risk signal Marcus and Claire need to act on quickly.                          |
| **Expiry Risk Count**           | How many supply batches at a clinic were flagged as approaching their expiry date during the month.       | A waste and compliance risk signal — flags supply that needs to be used or disposed of before it expires.      |

Everything below this point exists only to compute these four numbers correctly, reliably, and auditable.

---

## 3. Source data

> **A quick schema check first:** this pipeline needs a cost value on `inbound_order_created` (e.g. a `unit_cost` or `total_cost` field in `properties`) to compute supply cost. If your telemetry schema from the earlier milestone doesn't have one yet, add it now — it's a natural extension of an existing mandatory event, not a new event type. As always, this field describes a supply cost, never a patient.

Your source is `telemetry_events`, filtered to the mandatory metrics already defined in your telemetry BRIEFING:

| `event_type`                | Feeds which KPI(s)                     |
| -------------------------------- | --------------------------------------------- |
| `inbound_order_created`        | Supply Cost per Clinic                         |
| `outbound_order_created`       | Supply Consumption Volume                       |
| `stock_threshold_triggered`    | Critical Stockout Frequency                     |
| `supply_expiry_flagged`        | Expiry Risk Count                               |

You don't need any event outside this list for v1 — resist the urge to widen scope. In particular, do not join against any patient-level table.

---

## 4. Required aggregation

- **Grain:** one row per `clinic_id` per calendar month (`month_start` = the first day of the month, UTC).
- **Dimensions:** `clinic_id`, `country` (`US`/`UK`), `month_start`.
- **Computed fields per row (each maps directly to a KPI from section 2):**
  - `total_supply_cost` — Supply Cost per Clinic: sum of `inbound_order_created` costs for the month
  - `supply_consumption_count` — Supply Consumption Volume: count of `outbound_order_created` for the month
  - `critical_stockout_count` — Critical Stockout Frequency: count of `stock_threshold_triggered` for the month
  - `expiry_risk_count` — Expiry Risk Count: count of `supply_expiry_flagged` for the month
  - `currency` — `USD` or `GBP`, matching the clinic's country. **Do not convert currencies in this pipeline** — that is a v2 concern once you have an FX rate source.

---

## 5. Destination table

Create this table under a dedicated `reporting` schema — never write into `telemetry_events`:

```sql
create table reporting.monthly_clinic_supply_performance (
  id uuid primary key default gen_random_uuid(),
  clinic_id text not null,
  country text not null,
  month_start date not null,
  total_supply_cost numeric not null default 0,
  supply_consumption_count integer not null default 0,
  critical_stockout_count integer not null default 0,
  expiry_risk_count integer not null default 0,
  currency text not null,
  computed_at timestamptz not null default now(),
  unique (clinic_id, month_start)
);
```

The `unique (clinic_id, month_start)` constraint is what your idempotency strategy (upsert) should rely on.

---

## 6. New reporting endpoint

Expose this pipeline's output through a **new** module, `services/reporting/`, separate from `services/telemetry/`:

- `GET /reporting/monthly-clinic-supply-performance` — accepts optional `month_start` (defaults to the most recent computed month); returns all clinics for that month:

```json
{
  "month_start": "2026-07-01",
  "clinics": [
    {
      "clinic_id": "austin-north",
      "country": "US",
      "total_supply_cost": 18420.50,
      "supply_consumption_count": 340,
      "critical_stockout_count": 1,
      "expiry_risk_count": 4,
      "currency": "USD"
    }
  ]
}
```

- `GET /reporting/pipeline-runs/latest` — status and metadata of the last pipeline run (this can be the same pattern you'll reuse for any future pipeline).
- `POST /reporting/pipeline-runs` — triggers a manual run.

---

## 7. Business constraints

- No field in this pipeline's output — table, endpoint response, or log — may ever contain a patient identifier, diagnosis, or any real or simulated PHI. Aggregation stays at the `clinic`/`department` level.
- Never mix currencies in a single aggregate row — `USD` (US clinics) and `GBP` (UK clinics) are reported separately, side by side, not summed together.
- This pipeline reads `telemetry_events` **read-only**. It never writes back to it.
- `services/telemetry/analysis.py` and `GET /telemetry/report` are out of scope for this milestone — do not modify them.