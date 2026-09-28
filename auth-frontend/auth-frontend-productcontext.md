# Product Context: Frontend Authentication Architecture (AUTH-02)

## 1. Scope & Strategy
HealthCore operates a high-growth cross-border network of 12 multi-disciplinary clinics across the United States and the United Kingdom, led by CEO Dr. Sandra Okonkwo. Historically, operational tools have been isolated by market lines—running split electronic medical records, discrete regional tracking logs, and disconnected billing practices.

Our ongoing digital transition brings these operations under a unified Next.js monorepo workspace. The **AUTH-02** implementation forms our central security perimeter. By standardizing form behaviors, client-side route guards, and token life cycles, we build a predictable framework to process staff workflow data securely.

---

## 2. Clinical and Financial Workflows

### 🏥 Medical Staff Operations (Dr. Marcus Reid)
*   **Context**: Oversees roughly 120 clinical practitioners across all active physical sites.
*   **Workflow Impact**: Medical personnel require continuous, reliable app sessions that remain secure on shared clinic computers. Clean session clearing upon executing a logout prevents unauthorized route inspection between active practitioner rotations.

### 💰 Cross-Border Financial Lifecycle (Tom Callahan)
*   **Context**: Managing complex institutional billing states spanning commercial insurance matrices in the US and NHS frameworks in the UK.
*   **Workflow Impact**: Resolving profile actions cleanly via `/account/profile` and safeguarding internal dashboards using dedicated layouts keeps proprietary billing analytics completely hidden from public view.

### 👥 Onboarding & Compliance Records (Diane Foster)
*   **Context**: Tracks medical certification records and workforce compliance checks across 200 distributed employees.
*   **Workflow Impact**: The registration workflow ensures that newly onboarded clinicians are created on the system via `POST /users` and immediately logged in via `POST /auth/login`, creating a smooth first-day setup experience.

---

## 3. Regulatory Alignment & Data Standards
Under the leadership of Compliance Manager Claire Whitfield, HealthCore ensures absolute data privacy across regional jurisdictions (HIPAA in the US, UK GDPR in the UK).

Because token errors could lead to accidental exposure of sensitive records, frontend route isolation is an essential legal safeguard. The requirement to divide high-level configuration into a fundamental `User` core model (for system tracking such as email) and a separate, linked operational `Profile` model (for operational touchpoints like name and address) keeps identity fields partitioned safely. Furthermore, dropping tokens immediately following any `401 Unauthorized` response protects administrative interfaces from being accessed via stale browser cache footprints.

---

## 4. Acceptance Criteria & Core Experience Guardrails

*   **The "Zero Flash" Rule**: Because internal applications present core operational details, unauthenticated individuals must never see layout fragments, skeletons, or database text. Layout guard logic must completely block content visibility until token safety validation checks pass.
*   **Seamless Registration Flow**: New personnel profiles pass parameters sequentially through the `/register` workflow, executing registration and authentication as one seamless action before pushing the user to their dashboard.
*   **Explicit Data Architecture Mapping**: Evaluation relies heavily on the proper separation of fields. The profile interface must strictly display system records (email from `User`) and personal contact parameters (name/contact from the linked `Profile`), while enabling standard overrides via `PUT /profiles/me`.
*   **Targeted System Access**: The public website remains open globally for patient discovery, while internal applications remain hidden behind authentication views to safeguard company infrastructure.
