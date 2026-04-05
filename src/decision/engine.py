from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.decision.catalog import load_hypothesis_catalog
from src.decision.explain import build_explanation_payload
from src.decision.io import (
    load_core_features,
    load_hypothesis_outputs,
    load_performance_summary,
    write_decision_artifacts,
)
from src.decision.leaderboard import build_leaderboard
from src.decision.models import (
    DECISION_BUY_THRESHOLD,
    DECISION_SCHEMA_VERSION,
    DECISION_SELL_THRESHOLD,
    LEADERBOARD_SCORE_WEIGHTS,
)
from src.decision.recommender import compute_current_signals, compute_decision


def run_decision_engine(
    *,
    core_features_path: str | Path | None = None,
    hypotheses_dir: str | Path | None = None,
    performance_summary_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    catalog_path: str | Path | None = None,
) -> dict:
    core = load_core_features(path=core_features_path)
    performance_summary = load_performance_summary(path=performance_summary_path)
    hypothesis_ids = sorted(performance_summary.keys())
    hypothesis_outputs = load_hypothesis_outputs(hypothesis_ids, path=hypotheses_dir)
    catalog = load_hypothesis_catalog(hypothesis_ids, catalog_path=catalog_path)

    leaderboard = build_leaderboard(hypothesis_outputs, performance_summary, catalog)
    current_signals = compute_current_signals(leaderboard)
    decision = compute_decision(current_signals)
    evaluation_date = str(core["date"].max().date().isoformat())
    recommendation_payload = build_explanation_payload(
        current_signals=current_signals,
        decision=decision,
        evaluation_date=evaluation_date,
        catalog=catalog,
    )
    generated_at_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    report_warnings = _collect_report_warnings(core, leaderboard)

    report = {
        "artifact_metadata": {
            "schema_version": DECISION_SCHEMA_VERSION,
            "generated_at_utc": generated_at_utc,
        },
        "input_files_loaded": {
            "core_features": str(core_features_path or "data/processed/core_features.parquet"),
            "performance_summary": str(performance_summary_path or "data/hypotheses/performance_summary.json"),
            "hypotheses": [
                str((Path(hypotheses_dir) / f"{hypothesis_id}.parquet") if hypotheses_dir else f"data/hypotheses/{hypothesis_id}.parquet")
                for hypothesis_id in hypothesis_ids
            ],
        },
        "current_evaluation_date": evaluation_date,
        "thresholds": {
            "buy_threshold": DECISION_BUY_THRESHOLD,
            "sell_threshold": DECISION_SELL_THRESHOLD,
        },
        "scoring_formula": {
            "quality_score_weights": LEADERBOARD_SCORE_WEIGHTS,
            "decision_score": "sum(latest_signal * quality_weight for active hypotheses)",
        },
        "hypothesis_count": len(hypothesis_ids),
        "warnings": report_warnings,
    }

    out_dir = write_decision_artifacts(
        leaderboard=leaderboard,
        current_signals=current_signals,
        current_recommendation=recommendation_payload,
        decision_report=report,
        output_dir=output_dir,
    )

    top_hypothesis = leaderboard.iloc[0]["hypothesis_id"] if not leaderboard.empty else "n/a"
    active_count = int(current_signals["latest_active"].sum())
    print(f"Loaded hypothesis outputs: {len(hypothesis_ids)}")
    print("Built leaderboard.")
    print(f"Top hypothesis: {top_hypothesis}")
    print(f"Current active hypotheses: {active_count}")
    print(f"Decision score: {decision.decision_score:.2f}")
    print(f"Recommendation: {decision.recommendation}")
    print(f"Confidence: {decision.confidence:.2f}")
    print(f"Saved outputs to {out_dir}")

    return recommendation_payload


def _collect_report_warnings(core: pd.DataFrame, leaderboard: pd.DataFrame) -> list[str]:
    warnings: list[str] = []
    core_latest = core["date"].max().date().isoformat()
    leaderboard_dates = set(leaderboard["latest_date"].tolist())
    if len(leaderboard_dates) > 1:
        warnings.append("Hypothesis outputs are not aligned on a single latest date.")
    if len(leaderboard_dates) == 1 and core_latest not in leaderboard_dates:
        warnings.append("Latest hypothesis date differs from latest core feature date.")
    return warnings


def main() -> None:
    run_decision_engine()


if __name__ == "__main__":
    main()
