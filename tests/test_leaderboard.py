from __future__ import annotations

import pandas as pd

from src.decision.catalog import load_hypothesis_catalog
from src.decision.leaderboard import build_leaderboard


def test_ranks_hypotheses_descending_quality_score() -> None:
    summary = _summary()
    leaderboard = build_leaderboard(_outputs(), summary, load_hypothesis_catalog(sorted(summary.keys())))

    assert leaderboard["quality_score"].is_monotonic_decreasing
    assert leaderboard["rank"].tolist() == [1, 2, 3]


def test_handles_missing_optional_metric_columns_gracefully() -> None:
    summary = _summary()
    summary["h2_gold_lead"].pop("average_pnl")

    leaderboard = build_leaderboard(_outputs(), summary, load_hypothesis_catalog(sorted(summary.keys())))

    value = float(leaderboard.loc[leaderboard["hypothesis_id"] == "h2_gold_lead", "avg_pnl"].iloc[0])
    assert value == 0.0


def test_produces_deterministic_rank_order_on_ties() -> None:
    output = _outputs()
    summary = {
        "h1_mean_reversion": {"hit_rate": 0.5, "total_return": 1.0, "average_pnl": 0.01, "max_drawdown": -1.0, "number_of_trades": 10},
        "h2_gold_lead": {"hit_rate": 0.5, "total_return": 1.0, "average_pnl": 0.01, "max_drawdown": -1.0, "number_of_trades": 10},
    }
    output = {key: output[key] for key in summary}

    leaderboard = build_leaderboard(output, summary, load_hypothesis_catalog(sorted(summary.keys())))

    assert leaderboard["hypothesis_id"].tolist() == ["h1_mean_reversion", "h2_gold_lead"]


def test_favors_lower_drawdown_in_drawdown_component() -> None:
    summary = _summary()
    summary["h1_mean_reversion"]["max_drawdown"] = -1.0
    summary["h3_momentum"]["max_drawdown"] = -15.0

    leaderboard = build_leaderboard(_outputs(), summary, load_hypothesis_catalog(sorted(summary.keys())))
    ranked = leaderboard.set_index("hypothesis_id")

    assert ranked.loc["h1_mean_reversion", "quality_score"] > ranked.loc["h3_momentum", "quality_score"]


def _outputs() -> dict[str, pd.DataFrame]:
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-04-01", "2026-04-02"]),
            "signal": [0, 1],
            "regime": ["NORMAL", "NORMAL"],
            "active": [False, True],
            "forward_return": [0.01, 0.02],
            "pnl": [0.0, 0.02],
        }
    )
    return {
        "h1_mean_reversion": frame.copy(),
        "h2_gold_lead": frame.assign(signal=-1).copy(),
        "h3_momentum": frame.assign(signal=0, active=False).copy(),
    }


def _summary() -> dict[str, dict]:
    return {
        "h1_mean_reversion": {
            "hit_rate": 0.60,
            "total_return": 2.0,
            "average_pnl": 0.02,
            "max_drawdown": -2.0,
            "number_of_trades": 100,
        },
        "h2_gold_lead": {
            "hit_rate": 0.55,
            "total_return": 1.0,
            "average_pnl": 0.01,
            "max_drawdown": -3.0,
            "number_of_trades": 120,
        },
        "h3_momentum": {
            "hit_rate": 0.50,
            "total_return": 0.2,
            "average_pnl": 0.002,
            "max_drawdown": -8.0,
            "number_of_trades": 140,
        },
    }
