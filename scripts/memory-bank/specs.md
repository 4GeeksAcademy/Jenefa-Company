# Incident Analyzer

## Phase 1: Local Terminal Engine (/scripts)

- The core validation engine must be built as a standalone terminal script before integration.

### Execution & File Ingestion
- Location: /scripts/analyze.py
- Syntax: python analyze.py <path_to_csv>
- Parameter Handling: Dynamically reads any target dataset via command-line arguments.

### Strict Context Validation Layer
- A record is marked corrupt or invalid and completely excluded from core analytics if it contains missing columns, empty strings, or values outside the authorized ranges:
#### Mandatory System Fields: 
- incident_id, clinic_id, category, status, satisfaction_index.
#### Authorized HealthCore Categories (category):
  - Clinical Operations
  - Patient Experience
  - Revenue Cycle
  - Compliance
  - Workforce
#### Authorized Status Lifecycle Map (status):
- Open Bin: Open | In_Progress
- Closed Bin: Resolved
- Discarded Bin: Escalated

### Metric Calculations (Valid Records Only)
#### Processing Accounting 
- Separate totals for total valid versus total invalid entries.
#### Category Breakdown 
- Total incident counts mapped to each of the 5 authorized categories.
#### Status Lifecycle Breakdown
- Total distribution counts across the open, closed, and discarded equivalent bins.
#### Satisfaction Index
- The math average of all numeric entries inside the satisfaction_index field—strictly limited to cases in the closed (Resolved) status. Missing or blank entries must be omitted.

### Diagnostic Logging, Interactive Hook, and Export
- Terminal Display: Output a clean text dashboard using standard text layout lines.
- Error Log: Print a comprehensive summary explaining exactly how many invalid records were skipped and why (e.g., missing field, out-of-range value).
- Interactive Export Trigger: Prompt the administrator: Export results to CSV? [y / n].
- Data Flattening: Saving writes to results.csv with a flat format containing one metric calculation per row.

## Phase 2 : Web Platform Integration
- Once the local python verification engine calculations perfectly mirror your internal targets, port that code directly into the network platform ecosystem.

                  ┌──────────────────────────────┐
                  │   React Component Client     │
                  │        (/uis/web)            │
                  └──────────────┬───────────────┘
                                 │
              POST /api/incidents/analyze (multipart/form-data)
              GET /api/incidents/results/export (CSV streaming)
                                 │
                                 v
                  ┌──────────────────────────────┐
                  │    FastAPI Application       │
                  │       (/services/api)        │
                  └──────────────┬───────────────┘
                                 │
               Evaluates context against data streams
                                 v
                  ┌──────────────────────────────┐
                  │    Shared Core Validator     │
                  └──────────────────────────────┘

### Backend Engine (/services/api)
#### Endpoint POST /api/incidents/analyze:
- Ingests the data array stream via standard multipart/form-data.
- Runs the same strict validation script logic to isolate bad records from analytics data.
- Responds immediately with a structured JSON packet carrying summary metrics, category blocks, status lifecycles, and validation tracking blocks.
#### Endpoint GET /api/incidents/results/export:
- Generates and downloads a compiled results.csv file using a flat structural format.
#### Error Response Matrix:
- HTTP 400 (Bad Request): Triggered by unreadable data headers, zero-byte uploads, or mismatched layouts, returning a clear error description.

### UI View Workspace (/uis/web)
#### Navigation Tree: 
- Mounts a direct link to the Incident Analysis page inside the sidebar or main menu.
#### File Target Box: 
- Includes a drag-and-drop container file zone that streams documents straight to the target API parsing engine.
#### Dynamic Analytics Panel: 
- Displays real-time summary blocks containing general metrics, category breakdowns, status summaries, and satisfaction index scores.
#### Download Trigger: 
- Adds an active user button that links to the export download endpoint to pull reports seamlessly.
#### Diagnostic Banner: 
-Displays an alerts section when errors occur, highlighting the number of corrupt entries found along with clear reasons for their failure.
