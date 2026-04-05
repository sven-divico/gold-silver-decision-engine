from __future__ import annotations

import numpy as np
import pandas as pd

from src.decision.models import LEADERBOARD_SCORE_WEIGHTS, HypothesisDefinition


def build_leaderboard(
    hypothesis_outputs: dict[str, pd.DataFrame],
    performance_summary: dict[str, dict],
    catalog: dict[str, HypothesisDefinition],
) -> pd.DataFrame:
    rows: list[dict] = []
    for hypothesis_id, metrics in performance_summary.items():
        if hypothesis_id not in hypothesis_outputs:
            raise ValueError(f"Hypothesis output missing for {hypothesis_id}")
        latest = hypothesis_outputs[hypothesis_id].iloc[-1]
        rows.append(
            {
                "hypothesis_id": hypothesis_id,
                "hypothesis_name": catalog[hypothesis_id].display_name,
                "total_return": float(metrics.get("total_return", 0.0)),
                "hit_rate": float(metrics.get("hit_rate", 0.0)),
                "avg_pnl": float(metrics.get("average_pnl", metrics.get("avg_pnl", 0.0))),
                "max_drawdown": float(metrics.get("max_drawdown", 0.0)),
                "num_trades": int(metrics.get("number_of_trades", metrics.get("num_trades", 0))),
                "latest_signal": int(latest.get("signal", 0)),
                "latest_regime": str(latest.get("regime", "UNKNOWN")),
                "latest_active": bool(latest.get("active", False)),
                "latest_date": pd.to_datetime(latest["date"]).date().isoformat(),
            }
        )
    leaderboard = pd.DataFrame(rows)
    return compute_quality_score(leaderboard)


def compute_quality_score(leaderboard: pd.DataFrame) -> pd.DataFrame:
    scored = leaderboard.copy()
    scored["hit_rate_norm"] = _normalize(scored["hit_rate"])
    scored["total_return_norm"] = _normalize(scored["total_return"])
    scored["avg_pnl_norm"] = _normalize(scored["avg_pnl"])
    scored["drawdown_score"] = _normalize_drawdown(scored["max_drawdown"])

    scored["quality_score"] = (
        LEADERBOARD_SCORE_WEIGHTS["hit_rate"] * scored["hit_rate_norm"]
        + LEADERBOARD_SCORE_WEIGHTS["total_return"] * scored["total_return_norm"]
        + LEADERBOARD_SCORE_WEIGHTS["avg_pnl"] * scored["avg_pnl_norm"]
        + LEADERBOARD_SCORE_WEIGHTS["drawdown_score"] * scored["drawdown_score"]
    )

    scored = scored.sort_values(
        by=["quality_score", "hit_rate", "total_return", "hypothesis_id"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)
    scored["rank"] = np.arange(1, len(scored) + 1)

    return scored[
        [
            "rank",
            "hypothesis_id",
            "hypothesis_name",
            "quality_score",
            "hit_rate",
            "total_return",
            "avg_pnl",
            "max_drawdown",
            "num_trades",
            "latest_signal",
            "latest_regime",
            "latest_active",
            "latest_date",
        ]
    ]


def _normalize(series: pd.Series) -> pd.Series:
    minimum = float(series.min())
    maximum = float(series.max())
    if maximum == minimum:
        return pd.Series([0.5] * len(series), index=series.index, dtype=float)
    return (series - minimum) / (maximum - minimum)


def _normalize_drawdown(drawdown: pd.Series) -> pd.Series:
    abs_drawdown = drawdown.abs()
    return 1.0 - _normalize(abs_drawdown)
