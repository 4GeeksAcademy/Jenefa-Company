from pathlib import Path

import pytest

from data.pipelines.sales_forecast import load_sales_data
from regression.model_evaluation import evaluate, temporal_splits

DATA_PATH = Path(__file__).parents[2] / "data" / "raw" / "healthcore_sales.csv"


def test_temporal_folds_are_forward_only_and_contiguous():
    data = load_sales_data(DATA_PATH)
    folds = list(temporal_splits(data))
    assert len(folds) == 5
    previous_validation_end = -1
    for train, validation in folds:
        assert train[-1] < validation[0]
        assert train[0] == 0
        assert validation[0] > previous_validation_end
        previous_validation_end = validation[-1]


def test_temporal_split_rejects_unsorted_data():
    data = load_sales_data(DATA_PATH).iloc[::-1].reset_index(drop=True)
    with pytest.raises(ValueError, match="sorted"):
        list(temporal_splits(data))


def test_evaluation_writes_required_artifacts_and_metrics(tmp_path):
    result = evaluate(load_sales_data(DATA_PATH), tmp_path)
    assert len(result.cv_metrics) == 5
    assert {"train_mae", "validation_mae", "train_rmse", "validation_rmse"} <= set(result.cv_metrics)
    assert result.classification in {"Well Fitted", "Underfitting", "Overfitting"}
    assert result.figure_path.exists()
    assert result.report_path.exists()
    assert "Mean ± Standard Deviation" in result.report_path.read_text()
