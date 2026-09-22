from pathlib import Path

import pandas as pd
import pytest

from data.pipelines.sales_forecast import load_sales_data, run, split_by_years


DATA_PATH = Path(__file__).parents[2] / "data" / "raw" / "healthcore_sales.csv"


def test_split_obeys_eight_two_boundary_and_has_no_leakage():
    data = load_sales_data(DATA_PATH)
    years = sorted(data["month"].dt.year.unique())
    train, test = split_by_years(data, years[0], years[7], years[8], years[9])

    assert len(train["month"].dt.year.unique()) == 8
    assert len(test["month"].dt.year.unique()) == 2
    assert train["month"].dt.year.max() < test["month"].dt.year.min()
    assert set(train.index).isdisjoint(test.index)


def test_split_rejects_overlapping_periods():
    data = load_sales_data(DATA_PATH)
    with pytest.raises(ValueError):
        split_by_years(data, 2016, 2019, 2019, 2020)


def test_run_produces_metrics_predictions_and_visualization(tmp_path):
    result = run(DATA_PATH, tmp_path)

    assert result.train_years == (2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023)
    assert result.test_years == (2024, 2025)
    assert set(result.metrics) == {"mse", "psi", "gini", "k2", "mae"}
    assert len(result.predictions) == 24
    assert result.figure_path.exists()
    assert (tmp_path / "sales_forecast_predictions.csv").exists()
