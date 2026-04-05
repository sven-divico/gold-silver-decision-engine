from __future__ import annotations

import pandas as pd

from src.decision.models import DECISION_BUY_THRESHOLD, DECISION_SELL_THRESHOLD, RecommendationResult


def compute_current_signals(leaderboard: pd.DataFrame) -> pd.DataFrame:
    current = leaderboard.copy()
    total_quality = float(current["quality_score"].sum())
    if total_quality <= 0:
        current["quality_weight"] = 1.0 / len(current)
    else:
        current["quality_weight"] = current["quality_score"] / total_quality

    active = current["latest_active"].astype(bool)
    current["contribution"] = 0.0
    current.loc[active, "contribution"] = (
        current.loc[active, "latest_signal"] * current.loc[active, "quality_weight"]
    )
    return current


def compute_decision(current_signals: pd.DataFrame) -> RecommendationResult:
    decision_score = float(current_signals["contribution"].sum())
    recommendation = map_recommendation(decision_score)
    confidence = compute_confidence(current_signals, decision_score)
    return RecommendationResult(
        recommendation=recommendation,
        decision_score=decision_score,
        confidence=confidence,
    )


def map_recommendation(score: float) -> str:
    if score >= DECISION_BUY_THRESHOLD:
        return "BUY"
    if score <= DECISION_SELL_THRESHOLD:
        return "SELL"
    return "HOLD"


def compute_confidence(current_signals: pd.DataFrame, decision_score: float) -> float:
    active_mask = current_signals["latest_active"].astype(bool)
    max_possible_score = float(current_signals.loc[active_mask, "quality_weight"].sum())
    if max_possible_score <= 0:
        return 0.0
    confidence = abs(decision_score) / max_possible_score
    return float(min(1.0, max(0.0, confidence)))
