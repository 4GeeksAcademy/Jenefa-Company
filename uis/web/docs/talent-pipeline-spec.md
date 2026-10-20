# HealthCore - Digital Candidate Sourcing

## Tech Stack
- Next.js (App Router), React, and TypeScript.
- Do not use any external state management libraries (Redux, Zustand, Jotai, Recoil, etc.). 
- Use Component-level state with hooks 
- Full-page browser reloads not allowed
- Every network connection must be handled asynchronously using explicit `async/await` syntax.
- All data-fetching operations must explicitly handle and display at least three states: `loading`, `success`, and `error`. 
- After any structural write action (`PATCH`, `PUT`, or `POST`), the local client-side UI state must update immediately to reflect mutations without forcing a full page refresh.

## Feature & View Specification

### Candidate List Page (`/`)
- Endpoint Resource: Pulls complete applicant collections from `GET /records`.
- Roster Data Metrics: Renders each candidate's full legal name, position applied for, active hiring status, and current application pipeline stage correctly at a single glance from data fetched from the API.
- Dynamic Search Bar: Includes a responsive text input filtering rows instantly in-memory by name or email without triggering page reloads.
- URL Parameter Syncing: Synchronizes category selection values for both Status and Stage filtering dynamically with the URL state using query parameters without full page reloads.

### Candidate Detail Page (`/candidates/[id]`)
- Endpoint Resource: Displays isolated full record lookup data fetched from `GET /records/:id` to make sure it loads and displays all fields for the correct candidate by ID.
- Roster Details Grid: Renders name, email, phone, position, LinkedIn, CV link, years of experience, status, stage, and application date.
- State Mutators (Inline Dropdowns):
  - Select dropdown updating current pipeline status from the detail view using `PATCH /records/:id`.
  - Select dropdown updating current pipeline stage from the detail view using `PATCH /records/:id`.
- Timeline Evaluation Stream:
  - Lists existing notes dynamically inside the detail view via `GET /records/:id/notes`.
  - Add Note: Appends a new evaluation entry via a textbox sending a payload to `POST /records/:id/notes`.
  - Delete Note: Renders an inline control on each note to permanently remove that entry via `DELETE /records/:id/notes/:note_id`.

### Candidate Management Forms
- Registration Form: Includes a fully structured form interface to register a new candidate entry via a form using `POST /records`.
- Modification Form: Includes an editor interface to correct existing candidate data via a form using `PUT /records/:id`.
- Validation & Lifecycle Rules: 
  - Implements strict validation on both forms to block empty or invalid required fields before submission.
  - Shows explicit success notices or error message feedback after each form submission attempt.
