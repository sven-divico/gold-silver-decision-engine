from __future__ import annotations

from typing import Any

import pandas as pd

from src.decision.models import REASON_SUMMARY_TEXT, HypothesisDefinition, RecommendationResult


def build_explanation_payload(
    current_signals: pd.DataFrame,
    decision: RecommendationResult,
    evaluation_date: str,
    catalog: dict[str, HypothesisDefinition],
) -> dict[str, Any]:
    active_rows = current_signals[current_signals["latest_active"].astype(bool)].copy()
    signal_rows = active_rows[active_rows["latest_signal"] != 0].copy()

    records: list[dict[str, Any]] = []
    for _, row in signal_rows.iterrows():
        records.append(
            {
                "hypothesis_id": row["hypothesis_id"],
                "hypothesis_name": str(row["hypothesis_name"]),
                "signal": int(row["latest_signal"]),
                "regime": str(row["latest_regime"]),
                "active": bool(row["latest_active"]),
                "weight": float(row["quality_weight"]),
                "contribution": float(row["contribution"]),
                "reason_code": reason_code_for_signal(
                    hypothesis_id=str(row["hypothesis_id"]),
                    signal=int(row["latest_signal"]),
                    catalog=catalog,
                ),
            }
        )

    supporting, opposing = split_supporting_opposing(records, decision.recommendation)

    return {
        "date": evaluation_date,
        "recommendation": decision.recommendation,
        "decision_score": round(decision.decision_score, 6),
        "confidence": round(decision.confidence, 6),
        "active_hypotheses": int(active_rows.shape[0]),
        "supporting_hypotheses": supporting,
        "opposing_hypotheses": opposing,
        "summary_text": render_summary_text(supporting, opposing, decision.recommendation),
    }


def split_supporting_opposing(
    records: list[dict[str, Any]],
    recommendation: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if recommendation == "SELL":
        supporting = [record for record in records if record["contribution"] < 0]
        opposing = [record for record in records if record["contribution"] > 0]
    else:
        supporting = [record for record in records if record["contribution"] > 0]
        opposing = [record for record in records if record["contribution"] < 0]
    return supporting, opposing


def render_summary_text(
    supporting: list[dict[str, Any]],
    opposing: list[dict[str, Any]],
    recommendation: str,
) -> str:
    if recommendation == "HOLD":
        if not supporting and not opposing:
            return "Hold signal due to no active directional hypotheses."
        return "Hold signal due to mixed hypothesis contributions."

    focus = supporting if supporting else opposing
    reason_texts = [REASON_SUMMARY_TEXT.get(item["reason_code"], item["reason_code"]) for item in focus]
    if not reason_texts:
        return f"{recommendation.title()} signal generated from weighted hypothesis consensus."
    joined = " ".join(reason_texts[:2])
    return f"{recommendation.title()} signal driven by: {joined}"


def reason_code_for_signal(
    hypothesis_id: str,
    signal: int,
    catalog: dict[str, HypothesisDefinition],
) -> str:
    mapping = catalog[hypothesis_id].reason_codes
    return mapping.get(signal, "no_directional_signal")
