from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.decision.engine import run_decision_engine


def test_current_recommendation_matches_golden_fixture(tmp_path: Path) -> None:
    input_dir = _write_fixture_inputs(tmp_path)
    output_dir = tmp_path / "decision_out"
    run_decision_engine(
        core_features_path=input_dir / "processed" / "core_features.parquet",
        hypotheses_dir=input_dir / "hypotheses",
        performance_summary_path=input_dir / "hypotheses" / "performance_summary.json",
        output_dir=output_dir,
    )

    actual = json.loads((output_dir / "current_recommendation.json").read_text(encoding="utf-8"))
    expected = _load_fixture("expected_current_recommendation.json")

    assert actual == expected


def test_leaderboard_order_matches_golden_fixture(tmp_path: Path) -> None:
    input_dir = _write_fixture_inputs(tmp_path)
    output_dir = tmp_path / "decision_out"
    run_decision_engine(
        core_features_path=input_dir / "processed" / "core_features.parquet",
        hypotheses_dir=input_dir / "hypotheses",
        performance_summary_path=input_dir / "hypotheses" / "performance_summary.json",
        output_dir=output_dir,
    )

    leaderboard = json.loads((output_dir / "leaderboard.json").read_text(encoding="utf-8"))
    actual_order = [row["hypothesis_id"] for row in leaderboard]
    expected_order = _load_fixture("expected_leaderboard_order.json")

    assert actual_order == expected_order


def _write_fixture_inputs(tmp_path: Path) -> Path:
    root = tmp_path / "input"
    processed = root / "processed"
    hypotheses = root / "hypotheses"
    processed.mkdir(parents=True, exist_ok=True)
    hypotheses.mkdir(parents=True, exist_ok=True)

    core_features = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-04-01", "2026-04-02"]),
            "gsr": [80.0, 79.0],
            "gsr_z_252d": [2.1, 1.9],
            "gsr_mom_20d": [0.04, 0.01],
            "gold_mom_20d": [0.05, 0.02],
            "silver_mom_20d": [0.01, 0.03],
            "gsr_ret_1d": [0.01, -0.01],
        }
    )
    core_features.to_parquet(processed / "core_features.parquet", index=False)

    _hypothesis_output(
        date_values=["2026-04-01", "2026-04-02"],
        signal=[0, 1],
        regime=["NORMAL", "NORMAL"],
        active=[False, True],
        out_path=hypotheses / "h1_mean_reversion.parquet",
    )
    _hypothesis_output(
        date_values=["2026-04-01", "2026-04-02"],
        signal=[0, -1],
        regime=["STRESS", "NORMAL"],
        active=[False, True],
        out_path=hypotheses / "h2_gold_lead.parquet",
    )
    _hypothesis_output(
        date_values=["2026-04-01", "2026-04-02"],
        signal=[0, 0],
        regime=["NORMAL", "NORMAL"],
        active=[False, False],
        out_path=hypotheses / "h3_momentum.parquet",
    )

    performance_summary = {
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
    (hypotheses / "performance_summary.json").write_text(
        json.dumps(performance_summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return root


def _hypothesis_output(
    *,
    date_values: list[str],
    signal: list[int],
    regime: list[str],
    active: list[bool],
    out_path: Path,
) -> None:
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(date_values),
            "signal": signal,
            "regime": regime,
            "active": active,
            "forward_return": [None] * len(date_values),
            "pnl": [None] * len(date_values),
        }
    )
    frame.to_parquet(out_path, index=False)


def _load_fixture(name: str):
    return json.loads((Path("tests") / "fixtures" / "decision" / name).read_text(encoding="utf-8"))
