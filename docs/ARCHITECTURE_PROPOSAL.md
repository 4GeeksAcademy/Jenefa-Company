# Backend Architecture Proposal: `HealthCore`

## Architectural Pattern:
- `Layered Domain-Driven Architecture` is required because the core business logic must remain completely decoupled from the third-party tools.
- This allows James Osei's 6-person tech team to build unified workflows without rewriting fundamental software layers when underlying regional provider systems change (US and UK).
- By isolating the business rules into a core layer and wrapping third-party EHRs in adapter layers, a unified patient record API can be made for Dr. Marcus Reid without altering third-party platforms we do not legally control.

## Proposed Folder Structure & Separation Criteria
- The directory below keeps the healthcore domains vertically separated and technically layered.

```text
/backend
├── app/
│   ├── core/        # Framework setups & shared configurations
│   │   ├── config.py     # Environment settings
│   │   ├── database.py   # Central data pipeline 
│   │   └── middleware/
│   │       └── audit_log.py # Global compliance audit trail
│   │
│   ├── domains/             # Business feature domains
│   │   ├── clinical/        # Clinical Operations(Dr.Reid)
│   │   │   ├── router.py    # Transport Layer(HTTP endpoint routes)
│   │   │   ├── schemas.py     # Data Validation Layer
│   │   │   ├── services.py    # Business Logic(AI doc assistance)
│   │   │   └── adapters/      # Infrastructure Adapters (EHR APIs)
│   │   │
│   │   ├── appointments/      # Patient Experience(Priya Nair)
│   │   │   ├── router.py      # Transport Layer(HTTP endpoint routes)
│   │   │   ├── schemas.py     # Data Validation Layer
│   │   │   └── services.py    # No-show forecasting
│   │   │
│   │   └── billing/           # Revenue Cycle Domain(Tom Callahan)
│   │       ├── router.py      # Transport Layer(HTTP endpoint routes)
│   │       ├── schemas.py     # Data Validation Layer
│   │       └── services.py    # Business Logic (Claims review)
│   │
│   └── main.py               
```

### Allocation of Responsibility: 
- High-level business rules inside services.py are kept isolated from technical transport protocols (router.py) and specific infrastructure details (adapters/).
- Vertical Domain Separation: Code is separated by operational business feature (clinical, appointments, billing), mirroring HealthCore's actual departments. This isolates work tracks so developers can scale or alter one business domain without breaking another.
- Horizontal Layer Responsibility: Inside each individual domain folder, responsibilities are split strictly by code function:
  - router.py (Transport Layer): Captures HTTP verb definitions, routes requests, and returns JSON payloads. No raw database queries or predictive models are found here.
  - schemas.py (Validation Layer): Employs Pydantic structures to sanitize inputs, ensuring unvetted data payloads cannot corrupt the core code layers.
  - services.py (Business Logic Layer): Executes rules like NLP note parsing or no-show forecasting entirely independent of database framework choices
  - ./adapters (Infrastructure Layer): Formats generic internal requests into the specific data shapes required by the mismatched third-party US and UK EHR engines

## FastAPI Endpoint & Router Organization
- Routes are explicitly grouped into sub-routers per domain rather than cluttering a single massive file.
### Router Blueprint & Grouping Criteria
- Clinical Operations Sub-Router (/api/v1/clinical): Groups routes managing cross-location medical timelines and AI administrative document parsing.
  - Concrete Routes:
    - GET /patient/{id}/history - Compiles an aggregated, cross-border patient timeline across regional EHR platforms.
    - POST /notes/assist - Automatically processes draft clinical transcripts using natural language processing.
- Patient Access Sub-Router (/api/v1/appointments): Groups paths handling online bookings and notification delivery logic to mitigate the 22% network no-show rate.
  - Concrete Routes:
    - POST /book - Unified online booking route replacing the legacy US phone system and UK manual diaries.
    - GET /analytics/risk-score - Identifies high-risk slots using predictive models to trigger proactive follow-ups.
- Revenue Operations Sub-Router (/api/v1/billing): Groups tracks managing insurance claims and cash streams to lower the 14% US claims denial rate.
  - Concrete Routes:
    - POST /claims/review - Pre-screens automated coding recommendations against insurance rules before submission.
    - GET /dashboard/realtime - Aggregates US commercial tracks and UK private pay into a single financial canvas for Tom Callahan.

## Research Sources and Standard FastAPI Conventions
- This design implements standard industry conventions and the FastAPI Best Practices.
### Modular Router Registration
- Following the official documentation, sub-routers are initialized locally inside their domains using router = APIRouter(), and then centralize cleanly into the core application using app.include_router() inside main.py.
### Explicit Dependency Isolation 
- To avoid global application tightly-coupled modules, resources like database sessions or logging handles are injected dynamically into endpoints using FastAPI's native functional framework via Depends().
### Pydantic Validation
- This structure mirrors the official recommendation to keep data transmission independent from data storage by strictly decoupling Pydantic schemas from database ORM models.

## Frontend & Backend Communication
- The user-facing analytical dashboards used by Dr. Okonkwo and department heads exist as a detached software entities from the Python API backend.
- API Communication: All data moving between the systems travels via secure, encrypted HTTPS connections using JSON formatting. The frontends consume data strictly by querying versioned backend endpoints (/api/v1/...).
- Cross-Origin Resource Sharing (CORS): Because the clinical dashboards and the central API operate on completely separate network origins, the backend employs FastAPI's native CORSMiddleware. A whitelist containing only the internal frontend system domain URLs rather than allowing insecure wildcard access (allow_origins=["*"]) to mitigate security exploits is declared explictly.
- Environment Variable Management: Secrets such as database strings, encryption salts, and compliance API keys are completely barred from git control. The backend parses system variables securely at runtime using pydantic-settings to guarantee distinct, secure boundaries between US-HIPAA and UK-GDPR hosting regions

## Risks and Points of Attention
- If the development team deviates from this proposed structural blueprint, two major critical points of failure could compromise HealthCore:
### Layer Bleeding & Legal Non-Compliance
- If developers shortcut the architecture by writing database mutations or raw external queries directly inside a router.py endpoint file, the web transport layer becomes tightly coupled to specific regional database mechanics.
- This breaks central audit logging (middleware/audit_log.py), directly violating HIPAA and UK GDPR data-tracking mandates.
### Circular Dependency Architecture Crashes
- In a cross-border ecosystem, modules frequently require shared context (e.g., the billing module validating patient details inside the clinical module). 
- If domains make direct, tightly coupled cross-imports into one another, Python's runtime engine will encounter circular dependency errors and crash on startup. 
- Teams must strictly route shared logic downward through core schemas or abstract messaging pipelines to preserve operational stability.