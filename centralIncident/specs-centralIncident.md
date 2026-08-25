# Technical Specifications: Incident Data Model, Backend & UI (HealthCore)

## Data Model Schema
The `Incident` entity must contain the following fields:

| Field Name | Data Type | Constraints / Allowed Values | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID / Int | Primary Key, Auto-generated | Unique identifier for each system incident report. |
| `title` | String | Required, Max length 255 | Brief title summarizing the incident. |
| `description`| Text | Required | Detailed explanation of the incident occurrence. |
| `category` | String | Required (Must match HealthCore Context) | System classification corresponding to the department tracking space. |
| `status` | String | Required, Enum | Current lifecycle state of the incident. |
| `origin` | String | Required, Enum | The reporting channel source. |
| `branch` | String | Required (Must match HealthCore Locations) | Managing clinic location code. Uses `central` for company-wide background bugs. |
| `created_at` | Timestamp | Auto-generated | Date and time when the incident was created. |
| `updated_at` | Timestamp | Auto-updated | Date and time of the last modification. |

## Integrity Constraints & HealthCore Domain Enums
* **Strict Context Synchronization**: Field names, categories, and branch location options must match the official HealthCore layout exactly.
* **Allowed Categories (`category`)**: Must strictly map to one of these 6 corporate domains:
  * `clinical_operations` (EHR desync, data visibility blocks).
  * `patient_experience` (Online booking, outreach/reminder bugs).
  * `revenue_cycle` (Claims submissions, insurance coding errors).
  * `compliance_governance` (Audit logs, data requests, security risk scores).
  * `people_workforce` (HR portal, credential verification checklists, CME tracker).
  * `technology` (Central API telemetry, data pipeline, server health check drops).
* **Allowed Location Branches (`branch`)**: Must strictly map to one of the 12 active HealthCore clinic markets or global HQ:
  * **US Region**: `texas_clinic_1`, `texas_clinic_2`, `texas_clinic_3`, `florida_clinic_1`, `florida_clinic_2`, `florida_clinic_3`, `georgia_clinic_1`, `georgia_clinic_2`, `georgia_clinic_3`.
  * **UK Region**: `london_clinic_1`, `london_clinic_2`, `manchester_clinic`.
  * **Global Backbone**: `central` (Non-location specific background infrastructure failures).
* **Status Enum Values**: `open`, `in_progress`, `resolved`, `discarded`.
* **Origin Enum Values**: `customer`, `branch`, `internal`.

---

## Historical Data Seed Script (`/scripts/seed_incidents.py`)
This script reads historical clinical tracking logs from the source CSV file and seeds them into the centralized database.
* **Schema Mappings**: Hardcode `origin: "customer"` to represent legacy user entries. Map CSV data $\rightarrow$ `title`, `date` $\rightarrow$ `created_at`, and `location` $\rightarrow$ `branch`. Convert past statuses using HealthCore's category map.
* **Idempotency**: Prevent duplicate database entries; running the script twice does not duplicate data.
* **Summary Validation Test**: After running the seed script, the `/api/incidents/summary` metrics for totals by model `status` and `category` must match the expected transformed sets of your valid-record baseline exactly.

---

## Backend API Endpoints (`/services`)
* **POST `/api/incidents`**: Validates and creates a new incident record in real-time. Returns correct HTTP codes for happy path (`201`) and error cases (`400`).
* **GET `/api/incidents`**: Lists all incident records. Supports optional filters: `status`, `origin`, `branch`, `category`.
* **GET `/api/incidents/{id}`**: Returns single incident details. Throws a `404` error code if it does not exist.
* **PATCH `/api/incidents/{id}/status`**: Updates the lifecycle `status`. Invalid status transitions that violate lifecycle workflow rules must be rejected with a `400` status code.
  * State transitions: `open` $\rightarrow$ `in_progress` or `discarded`; `in_progress` $\rightarrow$ `resolved` or `discarded`.
  * Final States: `resolved` and `discarded` are terminal and cannot be changed.
* **GET `/api/incidents/summary`**: Returns aggregated count metrics grouped by status, category, origin, and branch. Must return correct metrics (zero counts) even when there are no incidents.

---

## Frontend Specifications (`/uis`)

### 1. Incident Registration Form Page
* **Field Scope & Pre-Validation**: Includes all model fields and validates required fields on the client-side before submission to catch blank inputs safely.
* **Branch Options**: The `branch` input field is always visible and required, displaying options using explicit labels matching the 12 HealthCore clinics.
* **Conditional Styling Highlight**: When `origin` is `branch`, the branch input field is visually highlighted to remind the user they are reporting from a specific clinic location.
* **Submission States**: Loading states are clearly visible and the submit button is disabled during the request to prevent double-submitting if the API is slow.
* **Error Handling**: API errors are intercepted and shown in plain language to the user—never as technical or raw server text. If an error flags a specific field, the message appears next to that field.
* **Success Resolution**: Clears the form and displays a clear confirmation after a successful submission.

### 2. Incident List Panel Page
* **State Management**: The list page correctly handles all three possible views: `loading`, `empty`, and `with data`.
* **Filtering Controls**: Provide selection filters for `status`, `origin`, and `branch`.
* **Inline Status Modification Engine**: Allows updating status directly from the list view. If the network request fails, the visual status selection instantly reverts back to its previous value (optimistic rollback), and the user is notified.
* **Error Handling**: Displays an error message with a retry option if data fetching fails. If there are no incidents to show, displays an informative message.

### 3. Summary Panel Page
* **Metric Composition**: Displays the aggregated metrics from the `/api/incidents/summary` endpoint (totals by status, category, origin, and branch).
* **Asynchronous Resilience**: If data takes time to load or the request fails (e.g., server returns a 500 error), the panel displays the corresponding state gracefully without breaking or blocking the rest of the page.

---

## Cross-Cutting Monorepo Requirements
* **Zero Code Duplication**: Core data validation logic must be extracted completely into the global **`packages/shared/`** workspace directory. Both the independent historical seed script and the production backend API must import and reuse these exact functions.
* **Code Organization**: Code must be strictly organized according to the specified monorepo folder architecture (`/scripts/`, `/services/`, `/uis/`, `/packages/shared/`).

---

## Future Architecture Roadmap (Semantic Extension Foundation)
While not implemented in this milestone delivery, the text attributes (`title` and `description`) captured by this platform are structured to support future integration with **Vector Embeddings**. 
* The relational CRUD engine built here serves as the explicit storage foundation for generating dense text vectors.
* Future extensions will map these text blocks to a vector database for semantic search, duplicate clustering across branches, and automated category triage.
