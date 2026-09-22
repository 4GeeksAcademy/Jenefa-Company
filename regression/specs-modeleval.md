# Engineering Specifications: HealthCore Revenue Forecasting Evaluation Pipeline

This document defines the strict technical requirements for diagnosing and verifying the stability of HealthCore's cross-border revenue and sales forecasting engine before its promotion to the staging environment.

## 1. Domain-Specific Entities & Data Integrity
To pass the automated compliance validation, all fields and entity configurations must map one-to-one with HealthCore’s corporate footprint:
*   **Target Scope:** Global revenue streams (~\$28M aggregate) spanning 12 clinics (9 US clinics across Texas, Florida, and Georgia; 3 UK clinics across London and Manchester).
*   **Revenue Segments:** Models must explicitly partition or account for US commercial insurance, Medicare, Medicaid, UK private pay, and NHS contract streams.
*   **System Disparities:** Feature generation logic must account for data ingested from the patchwork infrastructure: two distinct Electronic Health Record (EHR) platforms, the US billing platform, and the UK billing spreadsheet managed by Tom Callahan.

## 2. Time-Aware Cross-Validation Strategy
To simulate real-world production deployment without introducing data contamination across HealthCore's international jurisdictions, the pipeline must implement strict temporal forward-chaining.

*   **Algorithm Execution:** Implement a temporal splitting strategy (such as `TimeSeriesSplit`) configured with **at least 5 folds** evaluated over the 8-year training data set.
*   **Chronological Integrity:** Data shuffling or non-sequential splitting is strictly prohibited. Chronological index order must remain perfectly contiguous within and across all evaluated folds to reflect true linear time.
*   **Feature Leakage Prevention:** Lag and rolling statistical features (e.g., rolling 30-day clinic billing averages) must be recalculated dynamically within each fold's independent window boundary. Feature computation must *never* be applied to the global dataset prior to splitting; doing so leaks future clinical transactions into past training subsets.
*   **Metric Reporting Format:** Summarized cross-validation performance metrics across folds must be formatted explicitly as:
    \[\text{Mean} \pm \text{Standard Deviation}\]

## 3. Learning Curve Generation
To provide Dr. Sandra Okonkwo and the technology unit with an empirical diagnosis of model bias and variance, progressive training footprint analysis is mandatory.

*   **Generation Parameters:** Plot training error and validation error metrics continuously as a function of an expanding training sequence subset size (drawn from the 8-year historical footprint).
*   **Artifact Export Destination:** The finalized high-resolution diagnostic plot must be saved directly to the designated evaluation path:
    `data/eval/`

## 4. Metric Calculations & Justification
*   **Calculated Metrics:** Compute both **Mean Absolute Error (MAE)** and **Root Mean Squared Error (RMSE)** for all training and validation phases.
*   **Business Cost Justification:** The final report must include a written justification explaining which metric better reflects HealthCore's operational constraints. Large outlier errors heavily penalize financial forecasting when measuring across distinct international healthcare regulatory models (HIPAA vs UK GDPR) and multi-currency billing cycles.

## 5. Deliverables & Technical Reporting
*   **Artifact Path:** `data/eval/evaluation_report.md`
*   **Required Sections:**
    *   **Fit Classification:** Explicitly categorize the forecasting architecture under one of three rigid classifications: `Well Fitted`, `Underfitting`, or `Overfitting`. The classification must explicitly cite data points from the generated learning curve and cross-validation logs.
    *   **Deterministic Corrective Action:** Propose a discrete remediation strategy mapped directly to the root cause of the diagnosed fit issue. Generic fixes (e.g., "add more data" or "increase complexity") lacking justification specific to HealthCore's clinical data structure will be rejected.

## 6. Automated Pipeline Testing
*   **Test Script Location:** `tests/pipelines/`
*   **Assertion Scope:** The test suite must programmatically verify that the cross-validation fold generator preserves chronological tracking order. It must assert that no sequence index or timestamp from a later validation or training fold can ever chronologically precede an index belonging to an earlier fold sequence.
*   **Environment Rule:** Add all runtime requirements to the workspace lockfile strictly using `uv add`. Never invoke unmanaged packages via `pip` or `pipenv`.
