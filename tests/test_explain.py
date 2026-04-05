from __future__ import annotations

import json

import pandas as pd

from src.decision.catalog import load_hypothesis_catalog
from src.decision.explain import build_explanation_payload
from src.decision.models import RecommendationResult


def test_supporting_and_opposing_are_separated_correctly() -> None:
    payload = build_explanation_payload(
        current_signals=_signals(),
        decision=RecommendationResult(recommendation="BUY", decision_score=0.2, confidence=0.5),
        evaluation_date="2026-04-02",
        catalog=_catalog(),
    )
    assert len(payload["supporting_hypotheses"]) == 1
    assert len(payload["opposing_hypotheses"]) == 1


def test_reason_codes_are_preserved() -> None:
    payload = build_explanation_payload(
        current_signals=_signals(),
        decision=RecommendationResult(recommendation="BUY", decision_score=0.2, confidence=0.5),
        evaluation_date="2026-04-02",
        catalog=_catalog(),
    )
    codes = {item["reason_code"] for item in payload["supporting_hypotheses"] + payload["opposing_hypotheses"]}
    assert "silver_cheap_vs_gold" in codes
    assert "silver_overextended_vs_gold" in codes


def test_summary_text_is_generated() -> None:
    payload = build_explanation_payload(
        current_signals=_signals(),
        decision=RecommendationResult(recommendation="BUY", decision_score=0.2, confidence=0.5),
        evaluation_date="2026-04-02",
        catalog=_catalog(),
    )
    assert isinstance(payload["summary_text"], str)
    assert payload["summary_text"]


def test_payload_is_json_serializable() -> None:
    payload = build_explanation_payload(
        current_signals=_signals(),
        decision=RecommendationResult(recommendation="BUY", decision_score=0.2, confidence=0.5),
        evaluation_date="2026-04-02",
        catalog=_catalog(),
    )
    json.dumps(payload)


def _signals() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "hypothesis_id": ["h1_mean_reversion", "h2_gold_lead", "h3_momentum"],
            "latest_signal": [1, -1, 0],
            "latest_active": [True, True, True],
            "hypothesis_name": ["H1", "H2", "H3"],
            "latest_regime": ["NORMAL", "STRESS", "NORMAL"],
            "quality_weight": [0.6, 0.3, 0.1],
            "contribution": [0.6, -0.3, 0.0],
        }
    )


def _catalog() -> dict:
    return load_hypothesis_catalog(["h1_mean_reversion", "h2_gold_lead", "h3_momentum"])
