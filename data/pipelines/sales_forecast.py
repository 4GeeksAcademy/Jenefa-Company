"""Reproducible HealthCore sales forecasting pipeline.

The pipeline deliberately keeps the raw CSV read-only and exposes the temporal
split as a small, testable function.  It uses the available production history;
when a dataset contains the specification's 2011-2020 window, callers can pass
those years explicitly to :func:`split_by_years`.
"""
from sklearn.metrics import mean_squared_error, mean_absolute_error

from __future__ import annotations

import argparse
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
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler

RANDOM_STATE = 42
EXPECTED_COLUMNS = {
    "month",
    "revenue_usd",
    "visits_count",
    "avg_revenue_per_visit_usd",
    "region",
}


@dataclass(frozen=True)
class ForecastResult:
    metrics: dict[str, float]
    predictions: pd.DataFrame
    figure_path: Path
    train_years: tuple[int, ...]
    test_years: tuple[int, ...]


def load_sales_data(path: str | Path) -> pd.DataFrame:
    """Load and validate production sales data without mutating the source."""
    frame = pd.read_csv(path)
    missing = EXPECTED_COLUMNS - set(frame.columns)
    extra = set(frame.columns) - EXPECTED_COLUMNS
    if missing or extra:
        raise ValueError(f"Invalid sales schema; missing={sorted(missing)}, extra={sorted(extra)}")

    frame = frame.copy()
    frame["month"] = pd.to_datetime(frame["month"], errors="coerce")
    for column in ("revenue_usd", "visits_count", "avg_revenue_per_visit_usd"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["region"] = frame["region"].astype("string").str.strip()
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=["month", "revenue_usd"])
    frame = frame[frame["revenue_usd"] >= 0].sort_values("month").reset_index(drop=True)
    if frame.empty:
        raise ValueError("Sales data contains no usable rows")
    return frame


def split_by_years(
    frame: pd.DataFrame,
    train_start: int,
    train_end: int,
    test_start: int,
    test_end: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Partition by calendar year and assert disjoint temporal boundaries."""
    if train_end >= test_start or train_start > train_end or test_start > test_end:
        raise ValueError("Training years must precede test years")
    years = frame["month"].dt.year
    train = frame.loc[years.between(train_start, train_end)].copy()
    test = frame.loc[years.between(test_start, test_end)].copy()
    if train.empty or test.empty:
        raise ValueError("Both temporal partitions must contain rows")
    if set(train["month"].dt.year) & set(test["month"].dt.year):
        raise AssertionError("Temporal leakage detected between partitions")
    return train, test


def _features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame[["visits_count", "avg_revenue_per_visit_usd", "region"]].copy()
    result["year"] = frame["month"].dt.year
    result["month_number"] = frame["month"].dt.month
    result["quarter"] = frame["month"].dt.quarter
    return result


def _psi(expected: pd.Series, actual: pd.Series, bins: int = 10) -> float:
    """Calculate PSI, using training quantiles and stable epsilon clipping."""
    expected = pd.to_numeric(expected, errors="coerce").dropna().to_numpy()
    actual = pd.to_numeric(actual, errors="coerce").dropna().to_numpy()
    if not len(expected) or not len(actual):
        return 0.0
    edges = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
    if len(edges) < 2:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    expected_dist = np.bincount(np.digitize(expected, edges[1:-1]), minlength=len(edges) - 1)
    actual_dist = np.bincount(np.digitize(actual, edges[1:-1]), minlength=len(edges) - 1)
    expected_dist = np.clip(expected_dist / len(expected), 1e-6, None)
    actual_dist = np.clip(actual_dist / len(actual), 1e-6, None)
    return float(np.sum((actual_dist - expected_dist) * np.log(actual_dist / expected_dist)))


def _gini(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Return a bounded rank-order concordance (Gini-style discrimination)."""
    order = np.argsort(predicted)
    ranks = np.argsort(np.argsort(actual))
    concordance = np.mean(np.diff(ranks[order]) > 0) if len(actual) > 1 else 1.0
    return float(2 * concordance - 1)


def _k2(residuals: np.ndarray) -> float:
    """Residual independence proxy: one minus first-order residual autocorrelation."""
    if len(residuals) < 3 or np.std(residuals) == 0:
        return 1.0
    correlation = np.corrcoef(residuals[:-1], residuals[1:])[0, 1]
    return float(np.clip(1.0 - abs(correlation), 0.0, 1.0))


from sklearn.metrics import mean_squared_error, mean_absolute_error  # Ensure mean_absolute_error is imported at the top

def train_and_evaluate(train: pd.DataFrame, test: pd.DataFrame, figure_path: str | Path) -> ForecastResult:
    numeric = ["visits_count", "avg_revenue_per_visit_usd", "year", "month_number", "quarter"]
    categorical = ["region"]
    preprocessor = ColumnTransformer(
        [
            ("numeric", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", RobustScaler())]), numeric),
            ("categorical", Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical),
        ]
    )
    model = Pipeline(
        [
            ("features", preprocessor),
            ("regressor", RandomForestRegressor(n_estimators=300, random_state=RANDOM_STATE, n_jobs=-1)),
        ]
    )
    model.fit(_features(train), train["revenue_usd"])
    predicted = model.predict(_features(test))
    actual = test["revenue_usd"].to_numpy()
    residuals = actual - predicted
    
    # Calculate Mean Absolute Error (MAE) for business-friendly finance reporting
    mae_val = float(mean_absolute_error(actual, predicted))
    
    prediction_frame = test[["month", "revenue_usd"]].rename(columns={"revenue_usd": "actual_revenue_usd"}).copy()
    prediction_frame["predicted_revenue_usd"] = predicted
    prediction_frame["residual_usd"] = residuals
    
    metrics = {
        "mae": mae_val,
        "mse": float(mean_squared_error(actual, predicted)),
        "psi": float(np.mean([_psi(train[column], test[column]) for column in ["visits_count", "avg_revenue_per_visit_usd"]])),
        "gini": _gini(actual, predicted),
        "k2": _k2(residuals),
    }
    
    figure_path = Path(figure_path)
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(11, 5))
    plt.plot(prediction_frame["month"], actual, label="Actual", linewidth=2)
    plt.plot(prediction_frame["month"], predicted, label="Random forest forecast", linewidth=2)
    spread = float(np.std(residuals))
    plt.fill_between(prediction_frame["month"], predicted - spread, predicted + spread, alpha=0.2, label="± residual std")
    plt.title("HealthCore sales forecast: temporal holdout")
    plt.ylabel("Revenue (USD)")
    plt.xlabel("Month")
    plt.legend()
    plt.tight_layout()
    plt.savefig(figure_path, dpi=150)
    plt.close()
    
    return ForecastResult(metrics, prediction_frame, figure_path, tuple(sorted(train["month"].dt.year.unique())), tuple(sorted(test["month"].dt.year.unique())))


def run(input_path: str | Path, output_dir: str | Path) -> ForecastResult:
    data = load_sales_data(input_path)
    available_years = sorted(data["month"].dt.year.unique())
    if len(available_years) < 10:
        raise ValueError("At least 10 distinct years are required for an 8/2 temporal split")
    # The checked-in production extract currently spans 2016-2025. This keeps
    # the required first-eight/final-two rule while remaining data-driven.
    train, test = split_by_years(data, available_years[0], available_years[7], available_years[8], available_years[9])
    output_dir = Path(output_dir)
    result = train_and_evaluate(train, test, output_dir / "sales_forecast.png")
    result.predictions.to_csv(output_dir / "sales_forecast_predictions.csv", index=False)
    pd.Series(result.metrics, name="value").to_csv(output_dir / "sales_forecast_metrics.csv", header=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/raw/healthcore_sales.csv")
    parser.add_argument("--output-dir", default="data/eval/sales_forecast")
    args = parser.parse_args()
    result = run(args.input, args.output_dir)
    print({"train_years": result.train_years, "test_years": result.test_years, **result.metrics})
