from __future__ import annotations

import pandas as pd

from src.decision.recommender import compute_current_signals, compute_decision, map_recommendation


def test_returns_buy_when_score_exceeds_positive_threshold() -> None:
    signals = compute_current_signals(_leaderboard([1, 1, 0], [True, True, True], [0.7, 0.2, 0.1]))
    decision = compute_decision(signals)
    assert decision.recommendation == "BUY"


def test_returns_sell_when_score_exceeds_negative_threshold() -> None:
    signals = compute_current_signals(_leaderboard([-1, -1, 0], [True, True, True], [0.7, 0.2, 0.1]))
    decision = compute_decision(signals)
    assert decision.recommendation == "SELL"


def test_returns_hold_near_zero() -> None:
    signals = compute_current_signals(_leaderboard([1, -1, 0], [True, True, True], [0.4, 0.4, 0.2]))
    decision = compute_decision(signals)
    assert decision.recommendation == "HOLD"


def test_inactive_hypotheses_contribute_zero() -> None:
    signals = compute_current_signals(_leaderboard([1, 1], [True, False], [0.5, 0.5]))
    assert float(signals.iloc[1]["contribution"]) == 0.0


def test_confidence_increases_with_stronger_consensus() -> None:
    weak = compute_decision(compute_current_signals(_leaderboard([1, -1], [True, True], [0.5, 0.5])))
    strong = compute_decision(compute_current_signals(_leaderboard([1, 1], [True, True], [0.5, 0.5])))
    assert strong.confidence > weak.confidence


def test_map_recommendation_boundaries() -> None:
    assert map_recommendation(0.25) == "BUY"
    assert map_recommendation(-0.25) == "SELL"
    assert map_recommendation(0.0) == "HOLD"


def _leaderboard(signals: list[int], active: list[bool], quality_scores: list[float]) -> pd.DataFrame:
    ids = [f"h{i}" for i in range(len(signals))]
    return pd.DataFrame(
        {
            "hypothesis_id": ids,
            "hypothesis_name": ids,
            "latest_signal": signals,
            "latest_active": active,
            "quality_score": quality_scores,
            "latest_regime": ["NORMAL"] * len(signals),
            "num_trades": [10] * len(signals),
            "hit_rate": [0.5] * len(signals),
            "total_return": [1.0] * len(signals),
            "avg_pnl": [0.01] * len(signals),
            "max_drawdown": [-1.0] * len(signals),
            "rank": list(range(1, len(signals) + 1)),
            "latest_date": ["2026-04-02"] * len(signals),
        }
    )
