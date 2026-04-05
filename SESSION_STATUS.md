# Session Status

## Current State

The project now includes a complete 3-step decision pipeline and UI integration:

- Step 1: Core feature dataset pipeline with validation.
- Step 2: Hypothesis engine with 3 modular signals, regime gating, backtests, and metrics.
- Step 3: Decision layer with leaderboard ranking, weighted active-signal aggregation, BUY/HOLD/SELL recommendation, confidence, and explainability payload.
- FastAPI calculator page now displays decision artifacts directly (recommendation, confidence, reasons, leaderboard).

All local tests currently pass.

## What Was Added Recently

### Decision UI Integration
- Added a new decision section on `/calculator` showing:
  - current recommendation
  - decision score
  - confidence
  - active hypothesis count
  - supporting vs opposing hypotheses with reason codes
  - leaderboard table preview
- Added graceful fallback messaging if artifacts are missing.

### Artifact Freshness + Guardrails
- Added decision artifact loading service with warnings for:
  - missing artifacts
  - schema-version mismatch
  - stale generation timestamps
  - stale recommendation date
  - warnings produced by the decision report itself
- Added artifact metadata to decision outputs:
  - `schema_version`
  - `generated_at_utc`

### Explainability Improvements
- Explanation entries now include:
  - `hypothesis_name`
  - `regime`
  - `active`
  - stable `reason_code`
  - weight and contribution

### Regression Coverage
- Added golden-fixture regression tests for:
  - `current_recommendation.json`
  - leaderboard hypothesis ordering
- Added decision-view guardrail tests for missing/stale/mismatched artifacts.

### Extensibility Hooks
- Added catalog-driven hypothesis metadata/reason-code loading.
- Decision layer now supports adding hypotheses without changing core recommendation interfaces.

## How To Run

1. Build core features:
   - `.venv/bin/python -m src.data.build_core_features`
2. Run hypothesis engine:
   - `.venv/bin/python -m src.hypotheses.engine`
3. Run decision engine:
   - `.venv/bin/python -m src.decision.engine`
4. Run app:
   - `.venv/bin/python -m uvicorn app.main:app --reload`
5. Run tests:
   - `.venv/bin/python -m pytest -q`

## Primary Outputs

- `data/processed/core_features.parquet`
- `data/hypotheses/*.parquet`
- `data/hypotheses/performance_summary.json`
- `data/decision/leaderboard.parquet`
- `data/decision/leaderboard.csv`
- `data/decision/leaderboard.json`
- `data/decision/current_signals.parquet`
- `data/decision/current_signals.csv`
- `data/decision/current_recommendation.json`
- `data/decision/decision_report.json`

## Key Files Added/Updated

- `src/decision/catalog.py`
- `src/decision/engine.py`
- `src/decision/explain.py`
- `src/decision/io.py`
- `src/decision/leaderboard.py`
- `src/decision/models.py`
- `app/services/decision_view.py`
- `app/routes/web.py`
- `app/templates/calculator.html`
- `app/static/css/styles.css`

## Test Status

Latest local run:

- `.venv/bin/python -m pytest -q`
- Result: `89 passed`

## Suggested Next Steps

1. Add a dedicated `/decision` page with filtering and full explainability drill-down.
2. Add a small automation/script to refresh Step 1 → Step 2 → Step 3 daily.
3. Add API endpoints that expose current recommendation and leaderboard JSON directly.
4. Add scenario-level smoke tests that verify UI rendering when artifacts are stale/missing.
