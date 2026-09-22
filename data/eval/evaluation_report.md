# HealthCore Revenue Forecast Evaluation

## Scope
The evaluation covers the 12 clinics and the US/UK revenue scope (approximately $28M). Revenue segments accounted for are: US commercial insurance, Medicare, Medicaid, UK private pay, NHS contract. The source extract should reconcile the two EHR platforms, US billing, and Tom Callahan's UK billing spreadsheet before promotion. No patient-level data is written to these artifacts.

## Temporal validation
Five chronological `TimeSeriesSplit` folds were used with no shuffling. Fold boundaries are in `temporal_cv_metrics.csv`; lag and rolling features were recomputed from each fold's available history.

| Metric | Mean ± Standard Deviation |
|---|---|
| Validation MAE | 119,721.67 ± 15,693.51 |
| Validation RMSE | 152,594.45 ± 22,541.69 |
| Training MAE | 21,978.09 ± 2,714.13 |
| Training RMSE | 28,033.45 ± 3,490.27 |

RMSE is the primary operational metric because squaring errors heavily penalizes a sudden denial spike or cross-border billing variance that can create staffing and cash-flow shortfalls. MAE remains the steady per-cycle error baseline.

## Learning curve and fit classification
**Fit classification: Overfitting.** At the largest training footprint, training RMSE was **$28,278.21** and validation RMSE was **$37,588.23**, a gap of **$9,310.02**. Across folds, validation RMSE was **152,594.45 ± 22,541.69**. See `learning_curve.png` and `learning_curve_metrics.csv` for the complete evidence.

## Deterministic corrective action
Regularize the forest and reduce clinic-specific memorization: tune max_depth/min_samples_leaf using the same temporal folds, then require a validation RMSE gap below 20% before staging.
