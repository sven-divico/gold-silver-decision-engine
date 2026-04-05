# Implementation Specification — Step 2
## Hypothesis Engine (MVP) — First 3 Signals + Backtest Framework

Version: v0.1  
Status: Ready for implementation  
Depends on: Step 1 (core dataset)  
Purpose: Implement the first version of the hypothesis engine that generates signals from the core dataset and evaluates them via backtesting.

---

## 1. Objective

Build the **first working hypothesis engine** that:

1. Loads the processed dataset from Step 1
2. Implements 3 core hypotheses as modular signal generators
3. Applies simple regime filters
4. Runs a walk-forward backtest
5. Outputs performance results per hypothesis

This step establishes the **core system logic**:
> hypotheses → signals → performance → comparison

This is the foundation for the later:
- leaderboard
- decision engine
- UI

---

## 2. Scope

### In scope
- hypothesis module structure
- 3 hypothesis implementations
- regime filter (basic)
- signal generation
- walk-forward backtest
- performance metrics
- result export

### Out of scope
- UI
- API ingestion
- multi-asset expansion
- advanced ML models
- microstructure indicators

---

## 3. Product Rationale

From research:

- No single indicator works across all regimes
- Gold leads, silver follows (in specific regimes)
- Ratio extremes alone are insufficient
- Liquidity stress drives major dislocations :contentReference[oaicite:0]{index=0}

Therefore:
- hypotheses must be **modular**
- performance must be **measured independently**
- signals must be **conditioned on regime**

---

## 4. Hypotheses (MVP Set)

Implement exactly these 3:

---

### H1 — Extreme Ratio Mean Reversion

**Logic:**
- If GSR is very high → silver cheap → expect compression
- If GSR is very low → silver expensive → expect widening

**Signal definition:**
```python
if gsr_z_252d > 2:
    signal = +1   # silver undervalued
elif gsr_z_252d < -2:
    signal = -1   # silver overvalued
else:
    signal = 0
```

### H2 — Gold Lead / Silver Lag

Logic:

Gold moves first
Silver catches up later

Signal definition:

if gold_mom_20d > threshold and silver_mom_20d < gold_mom_20d * 0.5:
    signal = +1
elif silver_mom_20d > threshold and gold_mom_20d < silver_mom_20d * 0.5:
    signal = -1
else:
    signal = 0
H3 — Ratio Momentum (Stress / Froth Detector)

Logic:

Fast widening → stress → silver cheap
Fast compression → froth → silver expensive

Signal definition:

if gsr_mom_20d > threshold:
    signal = +1
elif gsr_mom_20d < -threshold:
    signal = -1
else:
    signal = 0
5. Regime Filter (v1 — simple but critical)

Define a basic volatility proxy using GSR volatility:

gsr_vol_20d = gsr_ret_1d.rolling(20).std()

Define regimes:

Regime	Condition
NORMAL	vol <= rolling median
STRESS	vol > rolling median
Apply filters
Hypothesis	Active in regime
H1 Mean Reversion	NORMAL only
H2 Gold Lead	NORMAL + early trend
H3 Momentum	STRESS + transition

If regime not matched → signal = 0

6. Data Input

Load from:

data/processed/core_features.parquet

Required columns (must exist):

gsr
gsr_z_252d
gsr_mom_20d
gold_mom_20d
silver_mom_20d
gsr_ret_1d
7. Output Schema

Each hypothesis must output a dataframe:

column	description
date	timestamp
signal	-1 / 0 / +1
regime	NORMAL / STRESS
active	boolean
forward_return	future GSR return
pnl	signal * forward_return
8. Backtest Design
8.1 Forward return definition

Use 20-day forward return:

forward_return = gsr.shift(-20) / gsr - 1

Interpretation:

negative return → ratio compresses → silver outperforms
8.2 PnL logic
pnl = signal * (-forward_return)

Why:

if signal = +1 (silver cheap)
and ratio falls → positive outcome
8.3 Walk-forward approach
no lookahead bias
signals computed only using past data
forward return strictly future
9. Performance Metrics

Compute per hypothesis:

Required:
total return (sum pnl)
hit rate (% correct direction)
average pnl
max drawdown
number of trades
Optional:
Sharpe ratio
regime-specific performance
10. Output Files

Write:

1. Per-hypothesis signals
data/hypotheses/h1_mean_reversion.parquet
data/hypotheses/h2_gold_lead.parquet
data/hypotheses/h3_momentum.parquet
2. Performance summary
data/hypotheses/performance_summary.json

Example:

{
  "h1_mean_reversion": {
    "total_return": 0.42,
    "hit_rate": 0.61,
    "max_drawdown": -0.12
  }
}
11. Folder Structure
src/
  hypotheses/
    base.py
    h1_mean_reversion.py
    h2_gold_lead.py
    h3_momentum.py
    engine.py
    backtest.py
    metrics.py
12. Module Responsibilities
base.py
common interface for hypotheses
class Hypothesis:
    def generate_signal(self, df) -> pd.Series:
        pass
h1_mean_reversion.py
implements H1 logic
h2_gold_lead.py
implements H2 logic
h3_momentum.py
implements H3 logic
engine.py
loads dataset
applies all hypotheses
applies regime filters
backtest.py
computes forward returns
calculates pnl
runs evaluation loop
metrics.py
computes performance stats
13. Execution Entry Point
python -m src.hypotheses.engine

Expected output:

Loaded dataset: 1793-03-01 → 2026-04-02
Running H1...
Running H2...
Running H3...

Backtest complete.

H1 return: 0.38 | hit rate: 0.59
H2 return: 0.52 | hit rate: 0.63
H3 return: 0.21 | hit rate: 0.55

Saved results to data/hypotheses/
14. Testing Requirements

Create:

tests/
  test_h1.py
  test_h2.py
  test_h3.py
  test_backtest.py
Tests must verify:
signals generated correctly
no lookahead bias
forward returns correctly aligned
pnl calculation correct
regime filter disables signals properly
15. Acceptance Criteria

Step 2 is complete when:

All 3 hypotheses generate signals
Signals are regime-conditioned
Backtest runs end-to-end without errors
Performance metrics are computed
Outputs are saved to disk
Tests pass
Results are interpretable (not just numbers)
16. Design Principles (Critical)
1. Hypotheses are independent

Do NOT mix logic between hypotheses.

2. No hidden transformations

Signals must be transparent and explainable.

3. Avoid overfitting
fixed thresholds for v1
no optimization loops yet
4. Reproducibility

Same dataset → same results

17. Next Step (Preview)

Step 3 will introduce:

hypothesis leaderboard
signal aggregation (Buy / Hold / Sell)
explainability layer
18. Definition of Done

This step is complete when the system can:

load the dataset
generate hypothesis signals
evaluate them objectively
and persist results

This marks the transition from:
→ data pipeline
→ decision system foundation