# Product and Domain Context Mapping - HealthCore Digital Unit

This document establishes the precise business names, domain parameters, and baseline target datasets for the inventory system.

## 1. Domain Configuration Parameters
*   **Corporate System Context**: HealthCore Clinic Supply Network
*   **Product-Equivalent Model**: `MedicalSupply` (Code must use this name instead of a generic `Product` token)
*   **Inbound-Equivalent Model**: `InboundEntry`
*   **Outbound-Equivalent Model**: `OutboundExit`
*   **Partition Scope Key**: `clinic_id` (Calculated stock lines are partitioned across HealthCore's 12 facilities)
*   **Route Access Authorization Profile**: Restricted (All endpoints require active auth via TinyDB context lookup strings to ensure strict data governance)

## 2. SQLModel Database Structural Field Maps

### 2.1 MedicalSupply Base Table Model (`models.py`)
*   `id`: `int` (Primary Key)
*   `name`: `str` (e.g., "Sterile Surgical Gloves", "N95 Respirator Mask")
*   `sku`: `str` (Unique tracking identifier string, e.g., `HC-GLV-002`)
*   `clinic_id`: `str` (Core structural domain partition constraint tracking HealthCore's clinics)
*   `regulatory_tier`: `str` (Tracks asset compliance classifications under HIPAA or UK GDPR rules)

### 2.2 InboundEntry Table Model (`models.py`)
*   `id`: `int` (Primary Key)
*   `medical_supply_id`: `int` (Enforced Database Foreign Key: references `medicalsupply.id`)
*   `quantity`: `int` (Volume intake increment)
*   `clinic_id`: `str` (Target delivery clinic location identifier)
*   `created_at`: `datetime` (Timestamp log)
*   `user_uuid`: `str` (Audit identity string pulled directly from local TinyDB session records)

### 2.3 OutboundExit Table Model (`models.py`)
*   `id`: `int` (Primary Key)
*   `medical_supply_id`: `int` (Enforced Database Foreign Key: references `medicalsupply.id`)
*   `quantity`: `int` (Volume depletion amount requested)
*   `clinic_id`: `str` (Source deployment clinic location identifier)
*   `created_at`: `datetime` (Timestamp log)
*   `user_uuid`: `str` (Audit identity string pulled directly from local TinyDB session records)

---

## 3. Compliance Testing & Verification Seed Data

The tracking environments must be pre-populated with these baseline records to verify correct double-persistence connections.

### 3.1 TinyDB Seed State Context (Identity Access Cache)
```json
[
  { "user_uuid": "usr-hc-9901", "name": "Dr. Marcus Reid", "role": "Clinical Operations Director" },
  { "user_uuid": "usr-hc-2544", "name": "Austin Clinic Floor Nurse", "role": "Staff" }
]
```

### 3.2 Relational Seed Data Layout (Supabase Database Engine)

#### Core Stock Catalog (`MedicalSupply`)

| id | name | sku | clinic_id | regulatory_tier |
| :--- | :--- | :--- | :--- | :--- |
| **10** | Sterile Surgical Gloves | `HC-GLV-002` | `CLINIC-TX-01` | Standard Clinical |
| **20** | Controlled Sedative Vial | `HC-SED-882` | `CLINIC-UK-02` | High-Regulated (GDPR/HIPAA) |

#### Incoming Shipments Log (`InboundEntry`)

| id | medical_supply_id | quantity | clinic_id | user_uuid | Operational Note |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | 10 | 500 | `CLINIC-TX-01` | `usr-hc-9901` | Initial gloves intake for Austin hub |
| **2** | 20 | 50 | `CLINIC-UK-02` | `usr-hc-2544` | Scheduled sedative shipment London |
| **3** | 10 | 250 | `CLINIC-TX-01` | `usr-hc-2544` | Mid-month glove restock |

#### Outbound Shipments Log (`OutboundExit`)

| id | medical_supply_id | quantity | clinic_id | user_uuid | Operational Note |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | 10 | 300 | `CLINIC-TX-01` | `usr-hc-2544` | Distributed to exam rooms |
| **2** | 20 | 15 | `CLINIC-UK-02` | `usr-hc-9901` | Used in outpatient procedures |

### 3.3 Target Stock Aggregations (Validation Parity Check)
Queries to `/inventory/products` must return these exact figures computed at runtime:
*   **Sterile Surgical Gloves (`id: 10`)** [Partition Scope: `CLINIC-TX-01` (Austin)]:
    $$\text{Computed Balance} = (500 + 250) - 300 = \mathbf{450}$$
*   **Controlled Sedative Vial (`id: 20`)** [Partition Scope: `CLINIC-UK-02` (London)]:
    $$\text{Computed Balance} = 50 - 15 = \mathbf{35}$$
