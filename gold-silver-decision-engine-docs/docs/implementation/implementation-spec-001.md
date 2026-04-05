# Implementation Specification — Step 1
## Build the Unified Core Dataset and Feature Table for the Silver-vs-Gold Mispricing Engine

Version: v0.1  
Status: Ready for implementation  
Owner: Codex handoff  
Purpose: Create the first production-ready data layer for the app so later steps can backtest hypotheses and generate buy/hold/sell recommendations.

---

## 1. Objective

Implement the **core dataset pipeline** that ingests historical market data, aligns it into a single time series, computes the foundational relative-value features, and stores the result in a clean, reusable structure.

This step does **not** yet include:
- hypothesis scoring
- backtesting
- buy/hold/sell recommendation logic
- UI logic
- API-based daily updates

This step **does** include:
- loading gold and silver daily price history
- creating a unified time-indexed dataset
- computing the gold/silver ratio and first core features
- validating data quality
- exporting the feature dataset for downstream use

This specification is based on the research conclusion that the gold/silver ratio is foundational, but must later be conditioned on regime features rather than used alone. :contentReference[oaicite:0]{index=0}

---

## 2. Scope

### In scope
1. Read local historical data files:
   - `imports/xauusd_d.csv`
   - `imports/xagusd_d.csv`
2. Standardize schema
3. Align both series by date
4. Build a canonical daily dataframe
5. Compute core relative-value features
6. Validate missing values, duplicates, and price anomalies
7. Save outputs for later app modules

### Out of scope
- live market APIs
- macro indicators such as VIX, DXY, real yields
- COT / ETF flows
- hypothesis engine
- strategy evaluation
- frontend/dashboard

---

## 3. Product Rationale

The app’s long-term goal is to detect when silver is mispriced relative to gold. The research supports the following framing:

- Gold often acts as the primary macro/monetary signal
- Silver behaves as a higher-volatility hybrid of monetary + industrial exposure
- Relative dislocations often show up first in the **gold/silver ratio**
- Ratio extremes alone are insufficient, but they are the necessary first building block for all later logic :contentReference[oaicite:1]{index=1}

Therefore, Step 1 establishes the **canonical price and feature layer** that all later hypotheses will depend on.

---

## 4. Functional Requirements

### 4.1 Input files
The implementation must read these local files:

- `imports/xauusd_d.csv`
- `imports/xagusd_d.csv`

Assume both represent daily historical price data for:
- XAUUSD = gold
- XAGUSD = silver

### 4.2 Required minimum fields
The pipeline must support common OHLCV-style CSVs, but only requires:

- `Date`
- `Close`

If available, also preserve:
- `Open`
- `High`
- `Low`
- `Volume`

### 4.3 Canonical output dataframe
Create one canonical dataframe indexed by trading date with at least these columns:

#### Raw columns
- `date`
- `gold_close`
- `silver_close`

#### Derived columns
- `gsr` = `gold_close / silver_close`
- `gold_ret_1d`
- `silver_ret_1d`
- `gsr_ret_1d`
- `gold_mom_20d`
- `silver_mom_20d`
- `gsr_mom_20d`
- `mom_divergence_20d` = `gold_mom_20d - silver_mom_20d`
- `gsr_mean_252d`
- `gsr_std_252d`
- `gsr_z_252d`

### 4.4 Export outputs
The implementation must export:

1. Clean merged dataset  
   - `data/processed/core_features.parquet`
2. Optional CSV mirror for inspection  
   - `data/processed/core_features.csv`
3. Data quality report  
   - `data/processed/core_features_report.json`

---

## 5. Non-Functional Requirements

### 5.1 Deterministic
Running the pipeline twice on the same input files must produce identical outputs.

### 5.2 Transparent
The code must be easy to inspect and debug. Avoid overly abstract patterns at this stage.

### 5.3 Modular
Use small functions with clear responsibilities so later steps can extend the dataset with:
- VIX
- DXY
- real yields
- COT
- ETF flows

### 5.4 Robust
The pipeline must fail loudly on structural data problems rather than silently producing bad features.

---

## 6. Target Folder Structure

```text
project-root/
  imports/
    xauusd_d.csv
    xagusd_d.csv

  data/
    processed/
      core_features.parquet
      core_features.csv
      core_features_report.json

  src/
    data/
      load_prices.py
      build_core_features.py
      validate_core_features.py
    utils/
      logging.py
      paths.py

  notebooks/
    01_core_dataset_sanity_check.ipynb

  tests/
    test_load_prices.py
    test_build_core_features.py
    test_validate_core_features.py
7. Technical Design
7.1 Canonical schema
Input normalization rules

For each source file:

Parse Date as datetime
Convert column names to lowercase snake_case
Rename close column to:
gold_close for XAU
silver_close for XAG
Sort ascending by date
Drop duplicate dates, keeping the last occurrence
Ensure close prices are numeric
Merge strategy
Perform an inner join on date for v0.1
Rationale: downstream ratio calculations require both gold and silver prices on the same day
Record how many rows are removed due to date mismatch in the report JSON
Date handling
Keep only date, no intraday timestamp
Use naive daily timestamps consistently
Final dataframe must be sorted ascending by date
7.2 Feature definitions
7.2.1 Base relative feature
gsr = gold_close / silver_close
7.2.2 Daily returns

Use simple percentage returns:

gold_ret_1d = gold_close.pct_change(1)
silver_ret_1d = silver_close.pct_change(1)
gsr_ret_1d = gsr.pct_change(1)
7.2.3 Momentum features

Use 20-trading-day percentage change:

gold_mom_20d = gold_close / gold_close.shift(20) - 1
silver_mom_20d = silver_close / silver_close.shift(20) - 1
gsr_mom_20d = gsr / gsr.shift(20) - 1
mom_divergence_20d = gold_mom_20d - silver_mom_20d
7.2.4 Rolling ratio normalization

Use a 252-trading-day rolling window:

gsr_mean_252d = gsr.rolling(252).mean()
gsr_std_252d = gsr.rolling(252).std()
gsr_z_252d = (gsr - gsr_mean_252d) / gsr_std_252d
7.2.5 Null behavior

Expected nulls at the beginning of the series due to lookback windows are acceptable:

1-day returns: first row null
20-day momentum: first 20 rows null
252-day rolling stats: first 251 rows null

These should not be forward-filled.

8. Validation Rules
8.1 Required checks

The pipeline must run these checks and include results in core_features_report.json.

Schema checks
input file exists
required columns found
close column is numeric after coercion
Row integrity checks
no duplicate dates in final dataframe
final dataframe sorted ascending by date
no zero or negative close prices
no infinite values in derived features
Missing data checks
report number of missing values by column
report whether any missing values occur beyond expected lookback-induced nulls
Range / sanity checks

Flag but do not necessarily fail on:

daily returns larger than ±20%
ratio values outside a broad sanity band, e.g. 10 <= gsr <= 200
Merge diagnostics

Report:

number of rows in original gold file
number of rows in original silver file
number of overlapping merged rows
min and max date in each file
min and max date in merged output
8.2 Failure conditions

The pipeline must raise an error and stop if:

either input file is missing
required columns cannot be identified
merged dataframe is empty
any close price is zero or negative
duplicate dates remain after normalization
more than 5% of non-lookback rows have unexplained missing values in critical columns

Critical columns:

gold_close
silver_close
gsr
9. Implementation Plan
9.1 Module responsibilities
src/data/load_prices.py

Responsible for:

reading raw CSVs
normalizing schema
renaming columns
deduplicating by date
returning clean per-asset dataframes

Suggested public functions:

load_gold_prices(path) -> pd.DataFrame
load_silver_prices(path) -> pd.DataFrame
normalize_price_frame(df, asset_name) -> pd.DataFrame
src/data/build_core_features.py

Responsible for:

merging gold and silver data
computing all derived features
writing parquet/csv outputs

Suggested public functions:

merge_price_series(gold_df, silver_df) -> pd.DataFrame
add_core_features(df) -> pd.DataFrame
build_core_dataset(...) -> pd.DataFrame
src/data/validate_core_features.py

Responsible for:

data-quality checks
diagnostic metrics
JSON report generation

Suggested public functions:

validate_core_dataset(df, metadata) -> dict
write_validation_report(report, path) -> None
9.2 Execution entry point

Provide one runnable script, e.g.:

python -m src.data.build_core_features

Expected behavior:

Load raw data
Merge data
Compute features
Validate dataset
Save outputs
Print concise summary to console

Example console output:

Loaded gold rows: 4,812
Loaded silver rows: 4,810
Merged rows: 4,805
Date range: 2006-01-03 to 2025-12-31
Validation: PASSED
Saved: data/processed/core_features.parquet
Saved: data/processed/core_features.csv
Saved: data/processed/core_features_report.json
10. Testing Requirements

Implement at least these tests.

Unit tests
test_load_prices.py
loads valid CSV
rejects missing file
rejects missing required columns
removes duplicate dates correctly
sorts dates ascending
test_build_core_features.py
computes gsr correctly
computes returns correctly
computes momentum correctly
computes rolling z-score correctly
inner join drops non-overlapping dates correctly
test_validate_core_features.py
flags negative prices
flags empty merged dataset
allows expected lookback nulls
rejects unexplained missing values
11. Acceptance Criteria

Step 1 is complete when all of the following are true:

A single command builds the merged core dataset from the two import CSV files.
The output contains the required raw and derived columns.
The output is saved as parquet and CSV.
A JSON validation report is generated.
Tests for loading, feature generation, and validation pass.
The dataset is clean enough for Step 2: implementation of first hypotheses.
The code is modular and easy to extend with macro indicators later.
12. Recommended Implementation Notes
Use pandas first

For this stage, use pandas rather than premature optimization.

Prefer parquet as canonical output

CSV is only for inspection. Parquet should be the default downstream source.

Keep feature names stable

These column names will later be referenced by:

hypothesis modules
backtest modules
leaderboard logic
UI explanations

Do not rename them casually after implementation.

Avoid hidden transformations

Do not winsorize, smooth, or normalize returns beyond the explicit rolling features defined here.

13. Future Extension Hooks

This step should be implemented so the dataframe can later be extended with:

Macro regime fields
vix_close
dxy_close
real_yield_10y
Flow / positioning fields
silver_cot_net
gold_cot_net
silver_etf_holdings
gold_etf_holdings
Regime labels
regime_stress
regime_gold_first
regime_reflation
regime_froth

The research strongly supports a regime-conditioned framework rather than a static ratio model, so Step 1 should be kept extensible for that purpose.

14. Deliverables

Codex should deliver:

Source files implementing the dataset pipeline
Tests
Generated processed output files
A short README section explaining:
how to run the pipeline
expected input format
output files produced
15. Definition of Done

This task is done when the repository contains a working, tested pipeline that transforms the raw XAU/XAG daily CSVs into a validated core feature table ready for hypothesis implementation.

This completes the first foundational build step for the silver mispricing app.