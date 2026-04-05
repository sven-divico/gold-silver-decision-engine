from __future__ import annotations

from dataclasses import dataclass


DECISION_SCHEMA_VERSION = "decision.v1"
HYPOTHESIS_CATALOG_FILENAME = "hypothesis_catalog.json"

LEADERBOARD_SCORE_WEIGHTS = {
    "hit_rate": 0.40,
    "total_return": 0.30,
    "avg_pnl": 0.20,
    "drawdown_score": 0.10,
}

DECISION_BUY_THRESHOLD = 0.25
DECISION_SELL_THRESHOLD = -0.25

HYPOTHESIS_DISPLAY_NAMES = {
    "h1_mean_reversion": "Extreme Ratio Mean Reversion",
    "h2_gold_lead": "Gold Lead / Silver Lag",
    "h3_momentum": "Ratio Momentum",
}

HYPOTHESIS_REASON_CODES = {
    "h1_mean_reversion": {
        1: "silver_cheap_vs_gold",
        -1: "silver_expensive_vs_gold",
    },
    "h2_gold_lead": {
        1: "gold_leading_silver",
        -1: "silver_overextended_vs_gold",
    },
    "h3_momentum": {
        1: "ratio_spike_stress_discount",
        -1: "ratio_compression_froth_risk",
    },
}

REASON_SUMMARY_TEXT = {
    "silver_cheap_vs_gold": "Mean reversion sees silver as cheap vs gold.",
    "silver_expensive_vs_gold": "Mean reversion flags silver as expensive vs gold.",
    "gold_leading_silver": "Gold-lead signal indicates silver may catch up.",
    "silver_overextended_vs_gold": "Gold-lead divergence suggests silver is overextended.",
    "ratio_spike_stress_discount": "Ratio momentum indicates stress-driven silver discount.",
    "ratio_compression_froth_risk": "Ratio momentum warns of froth and compression risk.",
    "bullish_signal": "A bullish hypothesis signal supports silver outperformance.",
    "bearish_signal": "A bearish hypothesis signal supports silver underperformance.",
}


@dataclass(frozen=True)
class HypothesisDefinition:
    hypothesis_id: str
    display_name: str
    reason_codes: dict[int, str]


@dataclass(frozen=True)
class RecommendationResult:
    recommendation: str
    decision_score: float
    confidence: float
