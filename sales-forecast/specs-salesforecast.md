# Technical Specifications: Sales Forecasting Model Pipeline

## 1. Environment & Dependency Management
* **Environment Provisioning:** Verify tools using `uv --version`. Initialize the project environment at the root using `uv init` if `pyproject.toml` is missing.
* **Dependency Installation:** Add all required libraries exclusively via `uv add scikit-learn xgboost pandas matplotlib`. 
* **Tool Restrictions:** Do not use `pip install`, `pipenv`, or `poetry`.

## 2. Data Lifecycle & Preparation
* **Data Sources:** Load production data directly from `data/raw/healthcore_sales.csv` or the reference repository at `content/contexts/sales-forecasting/healthcore/healthcore_sales.csv`. Simulation of data is strictly forbidden.
* **Schema Validation:** Verify that incoming columns match the structural configurations defined in `CONTEXT-healthcore.md`.
* **Data Cleansing:** Handle all null, empty, or anomalous data fields before executing model training steps.
* **Feature Scaling:** Scale independent variables using robust techniques to prevent magnitude imbalances across multi-currency streams (USD/GBP).
* **Reproducibility Anchors:** Hardcode all `random_state` and `seed` variables across splits and algorithms to ensure absolute experiment reproducibility.

## 3. Temporal Partitioning & Leakage Prevention
* **8/2 Year Split Rule:** Allocate the first 8 years of historical data (2011–2018) for training. Save the final 2 years (2019–2020) exclusively for testing.
* **Temporal Isolation:** Prevent the training phase from accessing any data points or indices belonging to the designated test years.

## 4. Model Training & Architectural Selection
* **Selected Algorithm:** Random Forest Regressor (implemented via `scikit-learn`).
* **Selection Justification:** Chosen to fulfill the demand for high explainability by Finance Manager Tom Callahan. Random Forest averages an ensemble of independent decision trees. This makes its operational logic straightforward to explain to executive stakeholders compared to sequential gradient boosting (XGBoost), which requires extensive hyperparameter tuning and functions more like a black box.

## 5. Statistical Evaluation Matrix
Evaluate the final model on the test set using these four specific metrics:
* **Mean Squared Error (MSE):** Quantifies average squared prediction error. A low MSE alone is insufficient because it heavily penalizes outliers and fails to indicate whether the model captures structural trends or suffers from severe data drift.
* **Population Stability Index (PSI):** Monitors variations in the distribution of data features over time. This checks if patient behaviors changed between the training era and the testing era.
* **Gini Coefficient:** Evaluates the model's structural discrimination and rank-ordering capabilities.
* **K2 Score:** Assesses conditional independence and structural fit across the regression residuals.

## 6. Visualization Specifications
* **Trend Comparison:** Plot actual historical sales values against predicted performance across the 2-year testing window using `matplotlib`.
* **Variability Representation:** Render a shaded error band around the main prediction line to show the variance range. Avoid presenting a single optimistic point estimate.

## 7. Pipeline Testing & Quality Assurance
* **Test Suite Location:** File must be saved in `tests/pipelines/`.
* **Validation Criteria:** Implement a unit test that verifies the training/test split strictly obeys the 8-year / 2-year boundary and confirms zero data leakage across partitions.
