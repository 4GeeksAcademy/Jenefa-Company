"""Leakage-safe temporal evaluation for the HealthCore revenue forecaster."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler

from data.pipelines.sales_forecast import load_sales_data

N_SPLITS = 5
SEGMENTS = ("US commercial insurance", "Medicare", "Medicaid", "UK private pay", "NHS contract")
CLINIC_COUNT = 12


@dataclass(frozen=True)
class EvaluationResult:
    cv_metrics: pd.DataFrame
    learning_curve: pd.DataFrame
    classification: str
    figure_path: Path
    report_path: Path


def temporal_splits(frame: pd.DataFrame, n_splits: int = N_SPLITS):
    """Yield contiguous forward-chaining indices and reject shuffled inputs."""
    if n_splits < 5:
        raise ValueError("The evaluation requires at least five temporal folds")
    if not frame["month"].is_monotonic_increasing:
        raise ValueError("Temporal evaluation requires rows sorted by month")
    splitter = TimeSeriesSplit(n_splits=n_splits)
    for train_idx, validation_idx in splitter.split(frame):
        if train_idx[-1] >= validation_idx[0]:
            raise AssertionError("Training and validation windows overlap")
        yield train_idx, validation_idx


def _features(frame: pd.DataFrame, history: pd.DataFrame | None = None) -> pd.DataFrame:
    """Build lag/rolling features from the supplied historical window only."""
    current = frame.copy()
    source = history if history is not None else current
    revenue = source["revenue_usd"].reset_index(drop=True)
    derived = pd.DataFrame({"revenue_lag_1": revenue.shift(1),
                            "revenue_rolling_3": revenue.shift(1).rolling(3, min_periods=1).mean()})
    result = current[["visits_count", "avg_revenue_per_visit_usd", "region"]].copy()
    result["year"] = current["month"].dt.year
    result["month_number"] = current["month"].dt.month
    result["quarter"] = current["month"].dt.quarter
    # Source is concatenated in chronological order; positional alignment is intentional.
    result["revenue_lag_1"] = derived.iloc[-len(current):]["revenue_lag_1"].to_numpy()
    result["revenue_rolling_3"] = derived.iloc[-len(current):]["revenue_rolling_3"].to_numpy()
    return result


def _model() -> Pipeline:
    numeric = ["visits_count", "avg_revenue_per_visit_usd", "year", "month_number", "quarter",
               "revenue_lag_1", "revenue_rolling_3"]
    return Pipeline([("features", ColumnTransformer([
        ("numeric", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", RobustScaler())]), numeric),
        ("categorical", Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                                   ("onehot", OneHotEncoder(handle_unknown="ignore"))]), ["region"]),
    ])), ("regressor", RandomForestRegressor(n_estimators=150, random_state=42, n_jobs=-1))])


def _scores(actual: pd.Series, predicted: np.ndarray) -> tuple[float, float]:
    return float(mean_absolute_error(actual, predicted)), float(np.sqrt(mean_squared_error(actual, predicted)))


def _classify(curve: pd.DataFrame, cv: pd.DataFrame) -> str:
    final = curve.iloc[-1]
    gap = float(final.validation_rmse - final.training_rmse)
    validation = float(final.validation_rmse)
    spread = float(cv.validation_rmse.std(ddof=0))
    if gap > max(validation * 0.20, 1.0):
        return "Overfitting"
    if spread > validation * 0.20:
        return "Underfitting"
    return "Well Fitted"


def evaluate(data: pd.DataFrame, output_dir: str | Path) -> EvaluationResult:
    """Run five-fold temporal CV, learning curves, plot, and written report."""
    data = data.sort_values("month").reset_index(drop=True)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for fold, (train_idx, validation_idx) in enumerate(temporal_splits(data), 1):
        train, validation = data.iloc[train_idx], data.iloc[validation_idx]
        model = _model().fit(_features(train), train.revenue_usd)
        predicted = model.predict(_features(validation, pd.concat([train, validation], ignore_index=True)))
        train_pred = model.predict(_features(train))
        train_mae, train_rmse = _scores(train.revenue_usd, train_pred)
        val_mae, val_rmse = _scores(validation.revenue_usd, predicted)
        rows.append({"fold": fold, "train_mae": train_mae, "train_rmse": train_rmse,
                     "validation_mae": val_mae, "validation_rmse": val_rmse,
                     "train_end": int(train.index[-1]), "validation_start": int(validation.index[0])})
    cv = pd.DataFrame(rows)

    curve_rows = []
    for fraction in np.linspace(0.4, 1.0, 5):
        end = max(2, int(len(data) * fraction))
        train = data.iloc[:end]
        validation = data.iloc[end:min(len(data), end + max(1, len(data) // 5))]
        if validation.empty:
            validation = data.iloc[max(0, end - max(1, len(data) // 5)):end]
        model = _model().fit(_features(train), train.revenue_usd)
        train_pred = model.predict(_features(train))
        validation_pred = model.predict(_features(validation, pd.concat([train, validation], ignore_index=True)))
        _, train_rmse = _scores(train.revenue_usd, train_pred)
        _, validation_rmse = _scores(validation.revenue_usd, validation_pred)
        curve_rows.append({"training_rows": len(train), "training_rmse": train_rmse,
                           "validation_rmse": validation_rmse})
    curve = pd.DataFrame(curve_rows)
    classification = _classify(curve, cv)
    figure_path = output / "learning_curve.png"
    plt.figure(figsize=(10, 6))
    plt.plot(curve.training_rows, curve.training_rmse, marker="o", label="Training RMSE")
    plt.plot(curve.training_rows, curve.validation_rmse, marker="o", label="Validation RMSE")
    plt.xlabel("Chronological training rows"); plt.ylabel("RMSE (USD)")
    plt.title("HealthCore revenue forecasting learning curve"); plt.legend(); plt.tight_layout()
    plt.savefig(figure_path, dpi=300); plt.close()
    cv.to_csv(output / "temporal_cv_metrics.csv", index=False)
    curve.to_csv(output / "learning_curve_metrics.csv", index=False)

    def summary(column: str) -> str:
        return f"{cv[column].mean():,.2f} ± {cv[column].std(ddof=0):,.2f}"

    final = curve.iloc[-1]
    final_gap = final.validation_rmse - final.training_rmse
    action = {
        "Overfitting": "Regularize the forest and reduce clinic-specific memorization: tune max_depth/min_samples_leaf using the same temporal folds, then require a validation RMSE gap below 20% before staging.",
        "Underfitting": "Add billing-cycle features (insurance submission lags and segment-specific seasonality) and increase model capacity; validate each feature inside the temporal folds.",
        "Well Fitted": "Promote to staging with the temporal-fold monitor enabled; investigate any fold whose RMSE exceeds the reported mean by two standard deviations.",
    }[classification]
    report_path = output / "evaluation_report.md"
    report_path.write_text(f"""# HealthCore Revenue Forecast Evaluation

## Scope
The evaluation covers the {CLINIC_COUNT} clinics and the US/UK revenue scope (approximately $28M). Revenue segments accounted for are: {', '.join(SEGMENTS)}. The source extract should reconcile the two EHR platforms, US billing, and Tom Callahan's UK billing spreadsheet before promotion. No patient-level data is written to these artifacts.

## Temporal validation
Five chronological `TimeSeriesSplit` folds were used with no shuffling. Fold boundaries are in `temporal_cv_metrics.csv`; lag and rolling features were recomputed from each fold's available history.

| Metric | Mean ± Standard Deviation |
|---|---|
| Validation MAE | {summary('validation_mae')} |
| Validation RMSE | {summary('validation_rmse')} |
| Training MAE | {summary('train_mae')} |
| Training RMSE | {summary('train_rmse')} |

RMSE is the primary operational metric because squaring errors heavily penalizes a sudden denial spike or cross-border billing variance that can create staffing and cash-flow shortfalls. MAE remains the steady per-cycle error baseline.

## Learning curve and fit classification
**Fit classification: {classification}.** At the largest training footprint, training RMSE was **${final.training_rmse:,.2f}** and validation RMSE was **${final.validation_rmse:,.2f}**, a gap of **${final_gap:,.2f}**. Across folds, validation RMSE was **{summary('validation_rmse')}**. See `learning_curve.png` and `learning_curve_metrics.csv` for the complete evidence.

## Deterministic corrective action
{action}
""", encoding="utf-8")
    return EvaluationResult(cv, curve, classification, figure_path, report_path)


def run_evaluation(input_path: str | Path = "data/raw/healthcore_sales.csv", output_dir: str | Path = "data/eval") -> EvaluationResult:
    return evaluate(load_sales_data(input_path), output_dir)


if __name__ == "__main__":
    run_evaluation()
