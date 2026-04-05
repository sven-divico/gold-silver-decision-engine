# Implementation Specification — Step 3
## Leaderboard + Decision Engine + Explainability Layer

Version: v0.1  
Status: Ready for implementation  
Depends on:
- Step 1: core dataset pipeline
- Step 2: hypothesis engine + backtests

Purpose: Turn the existing hypothesis outputs into a user-facing decision layer that ranks hypotheses, aggregates active signals, and produces an explainable Buy / Hold / Sell recommendation for silver vs gold.

---

## 1. Objective

Build the first **decision-system layer** on top of the existing hypothesis engine.

This step must:

1. Load the existing hypothesis backtest outputs from `data/hypotheses/`
2. Build a **hypothesis leaderboard**
3. Score active signals from the current market state
4. Aggregate them into a single **Buy / Hold / Sell** recommendation
5. Generate a compact **explanation payload** describing why the recommendation was produced
6. Persist all outputs in stable machine-readable files for later UI integration

This step is the bridge from:

- data pipeline
- individual research hypotheses

to:

- ranked signal system
- current recommendation
- explainable app behavior

---

## 2. Scope

### In scope
- leaderboard generation
- hypothesis scoring / ranking
- active-signal aggregation
- recommendation rules
- explanation payload
- persisted outputs
- tests

### Out of scope
- frontend UI
- live API ingestion
- parameter optimization
- new hypotheses
- advanced ML weighting
- user authentication
- notification logic

---

## 3. Current State (Build on Existing Implementation)

The repository already has:

### Step 1
- validated core feature dataset
- `data/processed/core_features.parquet`

### Step 2
- 3 implemented hypotheses
- regime logic
- backtesting
- metrics
- engine entrypoint
- hypothesis outputs in `data/hypotheses/`

The next step must **build on top of the existing project**, not start over.

Do not rewrite Step 1 or Step 2.  
Do not duplicate hypothesis logic.  
Do not recompute historical backtests inside the decision layer unless needed for loading existing outputs.

The decision layer should consume existing artifacts as inputs.

---

## 4. Product Goal

The app goal is not just to backtest hypotheses.  
It must produce a practical output for the user:

- **BUY silver**
- **HOLD**
- **SELL / reduce silver exposure**

The recommendation must be:

- systematic
- explainable
- reproducible
- grounded in the current state of the leaderboard and active signals

---

## 5. Inputs

## 5.1 Required files
Load from existing outputs:

```text
data/processed/core_features.parquet
data/hypotheses/

Assume that data/hypotheses/ already contains:

per-hypothesis signal files
performance summary file from Step 2

If exact filenames differ slightly from the earlier spec, adapt to actual outputs already produced in the repo rather than forcing a breaking rename.

6. Deliverables

This step must produce:

1. Hypothesis leaderboard
data/decision/leaderboard.parquet
data/decision/leaderboard.csv
data/decision/leaderboard.json
2. Current recommendation
data/decision/current_recommendation.json
3. Current active signals
data/decision/current_signals.parquet
data/decision/current_signals.csv
4. Decision report
data/decision/decision_report.json
7. Core Concepts
7.1 Hypothesis leaderboard

The leaderboard ranks hypotheses by quality.

At minimum, each hypothesis must have:

identifier
latest signal
latest regime
number of historical trades
hit rate
total return
average pnl
max drawdown
quality score
rank
7.2 Current active signal

For each hypothesis, identify the latest available row and determine:

whether the hypothesis is active now
what signal it currently emits
whether it should contribute to the final recommendation
7.3 Final recommendation

Aggregate active weighted signals into one final recommendation:

BUY
HOLD
SELL
7.4 Explainability

Generate concise structured reasons such as:

"Mean reversion sees silver as cheap vs gold"
"Gold-lead signal indicates silver lagging"
"Momentum signal warns of froth / compression risk"

These reasons should be machine-readable first; UI-friendly rendering comes later.

8. Functional Requirements
8.1 Create leaderboard builder

Implement a module that reads the existing hypothesis outputs and creates a ranked leaderboard.

Required columns

The leaderboard must contain at least:

column	description
hypothesis_id	stable identifier
hypothesis_name	human-readable name
total_return	historical backtest result
hit_rate	percent correct
avg_pnl	mean pnl per trade
max_drawdown	downside profile
num_trades	number of active historical signals
latest_signal	most recent signal (-1/0/+1)
latest_regime	latest detected regime
latest_active	whether currently active
quality_score	composite ranking score
rank	1 = best
8.2 Define leaderboard scoring formula

Implement a simple explicit v1 scoring formula.

Required v1 rule

Use a transparent weighted score such as:

quality_score =
    0.40 * normalized_hit_rate +
    0.30 * normalized_total_return +
    0.20 * normalized_avg_pnl +
    0.10 * normalized_drawdown_score

Where:

normalized_drawdown_score should reward lower drawdowns
normalization should be cross-hypothesis and deterministic
if only 3 hypotheses exist, score still must remain stable and interpretable
Important

Do not introduce optimization or fitting loops.
Use a fixed formula only.

8.3 Identify current signals

For each hypothesis:

load its output dataframe
select the most recent available date
record:
signal
regime
active flag
forward-looking fields only if they are historical and already present
current decision logic must never use future returns
8.4 Recommendation logic

Implement a recommendation engine using current active signals and leaderboard weights.

Step A — Contribution per hypothesis

Each active hypothesis contributes:

contribution = latest_signal * quality_weight

Where:

quality_weight is derived from quality_score
inactive hypotheses contribute 0
Step B — Aggregate score
decision_score = sum(contribution_i)
Step C — Map score to recommendation

Default v1 mapping:

if decision_score >= 0.25:
    recommendation = "BUY"
elif decision_score <= -0.25:
    recommendation = "SELL"
else:
    recommendation = "HOLD"
Required behavior
thresholds must be constants in one place
easy to adjust later
deterministic
8.5 Confidence score

Add a confidence score for the final recommendation.

Suggested v1 approach

Confidence should increase when:

more hypotheses are active
active hypotheses agree in direction
higher-ranked hypotheses dominate the signal

A simple normalized value in [0, 1] is sufficient.

Example
confidence = min(1.0, abs(decision_score) / max_possible_score)

This is acceptable for v0.1 if implemented clearly.

8.6 Explanation payload

Generate structured explanation data.

Required fields in current_recommendation.json
{
  "date": "2026-04-02",
  "recommendation": "BUY",
  "decision_score": 0.41,
  "confidence": 0.67,
  "active_hypotheses": 2,
  "supporting_hypotheses": [
    {
      "hypothesis_id": "h1_mean_reversion",
      "signal": 1,
      "weight": 0.38,
      "contribution": 0.38,
      "reason_code": "silver_cheap_vs_gold"
    }
  ],
  "opposing_hypotheses": [],
  "summary_text": "Buy signal driven by silver undervaluation and gold-lead catch-up logic."
}
Reason codes

Each hypothesis must expose stable reason codes.

Example mapping:

h1_mean_reversion
silver_cheap_vs_gold
silver_expensive_vs_gold
h2_gold_lead
gold_leading_silver
silver_overextended_vs_gold
h3_momentum
ratio_spike_stress_discount
ratio_compression_froth_risk

The explanation system should use these codes rather than brittle ad-hoc strings.

9. Folder Structure

Add:

src/
  decision/
    leaderboard.py
    recommender.py
    explain.py
    engine.py
    models.py
    io.py

tests/
  test_leaderboard.py
  test_recommender.py
  test_explain.py
10. Module Responsibilities
10.1 src/decision/io.py

Responsible for:

loading processed core dataset
loading hypothesis outputs
loading existing performance summary
writing decision outputs

Suggested functions:

load_core_features()
load_hypothesis_outputs()
load_performance_summary()
write_decision_artifacts(...)
10.2 src/decision/leaderboard.py

Responsible for:

building the leaderboard dataframe
computing quality score
ranking hypotheses

Suggested functions:

build_leaderboard(hypothesis_outputs, performance_summary) -> pd.DataFrame
compute_quality_score(df) -> pd.DataFrame
10.3 src/decision/recommender.py

Responsible for:

computing weighted contributions
aggregating decision score
mapping to BUY/HOLD/SELL
computing confidence

Suggested functions:

compute_current_signals(...)
compute_decision_score(...)
map_recommendation(score) -> str
compute_confidence(...) -> float
10.4 src/decision/explain.py

Responsible for:

turning current signals into structured explanation objects
generating summary text from structured reasons

Suggested functions:

build_explanation_payload(...) -> dict
render_summary_text(...) -> str
10.5 src/decision/models.py

Optional but recommended:

typed constants
dataclasses / pydantic models for output payloads

This is especially useful because these outputs will later feed a UI.

10.6 src/decision/engine.py

Single entrypoint that:

loads inputs
builds leaderboard
computes current signals
produces recommendation
writes outputs
prints concise console summary
11. Output Specifications
11.1 leaderboard.json

Must contain all hypotheses ordered by rank.

Example:

[
  {
    "rank": 1,
    "hypothesis_id": "h2_gold_lead",
    "hypothesis_name": "Gold Lead / Silver Lag",
    "quality_score": 0.81,
    "hit_rate": 0.63,
    "total_return": 0.52,
    "avg_pnl": 0.014,
    "max_drawdown": -0.09,
    "num_trades": 118,
    "latest_signal": 1,
    "latest_regime": "NORMAL",
    "latest_active": true
  }
]
11.2 current_recommendation.json

Must contain:

date
recommendation
decision_score
confidence
active hypothesis count
supporting hypotheses
opposing hypotheses
summary text
11.3 decision_report.json

Must contain metadata such as:

input files loaded
current evaluation date
thresholds used
scoring formula used
hypothesis count
any warnings
12. Execution Entry Point

Provide:

python -m src.decision.engine

Expected behavior:

load existing artifacts
rank hypotheses
evaluate latest active signals
produce recommendation
save outputs

Example console output:

Loaded hypothesis outputs: 3
Built leaderboard.
Top hypothesis: h2_gold_lead
Current active hypotheses: 2
Decision score: 0.41
Recommendation: BUY
Confidence: 0.67
Saved outputs to data/decision/
13. Testing Requirements

Implement:

tests/test_leaderboard.py
tests/test_recommender.py
tests/test_explain.py
Required tests
13.1 Leaderboard tests
ranks hypotheses in descending quality score
handles missing optional metric columns gracefully
produces deterministic rank order
correctly favors lower drawdown in drawdown component
13.2 Recommender tests
BUY returned when weighted score exceeds positive threshold
SELL returned when weighted score exceeds negative threshold
HOLD returned near zero
inactive hypotheses contribute zero
confidence increases with stronger consensus
13.3 Explanation tests
supporting and opposing hypotheses separated correctly
reason codes preserved
summary text is generated
payload is JSON-serializable
14. Acceptance Criteria

Step 3 is complete when:

The system builds a ranked leaderboard from existing hypothesis outputs.
The system computes the current active signals using the latest available date.
The system generates a deterministic BUY / HOLD / SELL recommendation.
The recommendation includes a confidence score.
The recommendation includes structured explainability data.
Outputs are written to data/decision/.
Tests pass.
The implementation builds on current repo artifacts without duplicating Step 1 or Step 2 logic.
15. Design Principles
15.1 Keep the decision layer thin

This layer should consume outputs from Step 2, not re-implement hypotheses.

15.2 Prefer explicit formulas over smart abstractions

The user must be able to inspect why the system recommended BUY, HOLD, or SELL.

15.3 Stable identifiers matter

Use fixed hypothesis IDs and reason codes so later UI work is straightforward.

15.4 Reproducibility over sophistication

No dynamic optimization, no hidden calibration, no probabilistic black box.

16. Implementation Notes
Use actual repository outputs

If Step 2 output filenames differ slightly from the original ticket, adapt to what is already present in the repo.

Fail loudly on missing core artifacts

If required hypothesis outputs or performance files are missing, raise a clear error.

Keep thresholds centralized

Decision thresholds and leaderboard weights should live in one obvious place.

Preserve extensibility

The system should be easy to extend later when more hypotheses are added.

17. Future Extension Hooks

This step should be implemented so that later steps can add:

more hypotheses
regime-specific weighting
live daily refresh
UI dashboard
historical recommendation archive
alerting / notifications
parameter tuning

Do not hardcode assumptions that only work for exactly 3 hypotheses.

18. Definition of Done

This step is done when the repository can produce:

a ranked hypothesis leaderboard
a current decision score
a Buy / Hold / Sell recommendation
and a machine-readable explanation of why that recommendation was generated