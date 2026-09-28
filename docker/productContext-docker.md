# Product Context: Monorepo Development Environment

## 1. Problem Statement
The current monorepo operates reliably on individual, historically configured machine environments, but suffers from severe configuration drift. Onboarding new developers currently takes hours due to:
* Node.js (Alpine) and Python version conflicts across engineering machines.
* Lack of parity with globally installed system dependencies.
* Missing or undocumented environment configuration steps.

Development configurations must shift away from localized setup routines toward **Environment as Code (EaC)** to make environments entirely reproducible.

## 2. Company & Domain Context
**HealthCore** is an outpatient healthcare services company founded in 2011, operating a network of **12 clinics** across the US (Texas, Florida, Georgia) and the UK (London, Manchester). The organization employs roughly **200 people**, manages an annual revenue of **\$28 million**, and handles critical healthcare administration across highly fragmented legacy architectures.

To modernize this ecosystem, executive leadership under CEO **Dr. Sandra Okonkwo** established an internal software unit named **HealthCore Digital**. The squad's mandate is to engineer unified central APIs, AI-assisted clinical documentation systems, no-show predictive engines, and cross-border data integration tools. Because engineers in HealthCore Digital build systems that directly process Protected Health Information (PHI), local development sandboxes must be absolutely secure, isolated, and standardized.

## 3. Product Objectives
The core objective is to create a deterministic, reproducible development ecosystem versioned entirely alongside the codebase. 

* **Eliminate Onboarding Friction**: Shorten setup time for engineers joining HealthCore Digital down to a single terminal command.
* **Guarantee Parity**: Ensure that application environments run identically across all engineer machines, eliminating the "works on my machine" paradigm.
* **Retain Development Velocity**: Provide seamless hot-reloading capabilities across both frontend architectures and the backend service layer so developer workflows remain unaffected.

## 4. Scope of Work
This initiative containerizes the application layer of the monorepo exclusively for local development:
* **Frontend Layer (`/uis`)**: Consolidating both the public-facing site (`/website`) and the internal administration workspace (`/backoffice`) into a single UI container image running on separate ports.
* **Backend Layer (`/services`)**: Containerizing the FastAPI application utilizing `uv` for modern package management.
* **Orchestration Layer**: Managing networking, volume binds, environment injection, and local runtime lifecycles utilizing Docker Compose from the root directory.

## 5. User Persona & Success Metric
* **User**: Software engineers and data scientists within HealthCore Digital.
* **Success Metric**: A developer can execute `docker compose up` directly from the repository root on a clean machine and immediately access fully functional frontends and backends without manual dependency resolution.
