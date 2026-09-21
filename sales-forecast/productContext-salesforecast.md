# Product Context: HealthCore Sales Forecasting Feasibility Prototype

## 1. Executive Summary & Business Intent
**HealthCore**, an outpatient healthcare provider founded in 2011 and generating **\$28 million in annual revenue**, is evaluating a shift toward data-driven operational planning. The company currently operates **12 clinics** across the US and UK under the leadership of **Dr. Sandra Okonkwo**. Executive decisions currently depend on disparate, lagging weekly reports. 

This project is a critical feasibility checkpoint driven by a Finance Request for Information (RFI). Before committing engineering resources to build a comprehensive real-time Executive Dashboard, the data team must prove that the company's historical sales data can reliably predict future revenue behavior within an acceptable margin of error.

## 2. User Personas & Stakeholder Goals
* **Dr. Sandra Okonkwo (CEO):** Needs highly accurate operational visibility to manage a multi-country network without relying on manual phone calls for basic KPIs.
* **Tom Callahan (Revenue Cycle & Billing Manager):** Seeks an explainable forecasting model that balances US insurance streams and UK billing configurations without introducing black-box calculations.
* **James Osei (CTO) & Tech Lead:** Require an isolated, reproducible, and verifiable codebase built using `uv` that integrates into HealthCore's evolving central data architecture.

## 3. Operational Constraints & Domain Context
* **Fragmented Infrastructure:** HealthCore's tech ecosystem features two separate EHR platforms, regional billing tools, and manual spreadsheets with no shared data layer. The forecasting model must ingest raw text data securely from `healthcore_sales.csv`.
* **Regulatory Compliance:** The pipeline must adhere to HIPAA (US) and UK GDPR (UK) data treatment boundaries managed by Compliance Director Claire Whitfield.
* **Strict Evaluation:** The model must prove its predictive power on a 2-year holding period without relying on memorized historical patterns. This ensures the business case remains solid before full dashboard development begins.
