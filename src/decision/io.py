from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.utils.paths import decision_data_dir, hypotheses_data_dir, processed_data_dir


def decision_output_dir() -> Path:
    return decision_data_dir()


def load_core_features(path: str | Path | None = None) -> pd.DataFrame:
    core_path = Path(path or (processed_data_dir() / "core_features.parquet"))
    if not core_path.exists():
        raise FileNotFoundError(f"Missing core features file: {core_path}")
    frame = pd.read_parquet(core_path)
    frame["date"] = pd.to_datetime(frame["date"], utc=False)
    return frame


def load_performance_summary(path: str | Path | None = None) -> dict[str, dict]:
    summary_path = Path(path or (hypotheses_data_dir() / "performance_summary.json"))
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing performance summary file: {summary_path}")
    return json.loads(summary_path.read_text(encoding="utf-8"))


def load_hypothesis_outputs(hypothesis_ids: list[str], path: str | Path | None = None) -> dict[str, pd.DataFrame]:
    base_path = Path(path or hypotheses_data_dir())
    outputs: dict[str, pd.DataFrame] = {}
    for hypothesis_id in hypothesis_ids:
        file_path = base_path / f"{hypothesis_id}.parquet"
        if not file_path.exists():
            raise FileNotFoundError(f"Missing hypothesis output file: {file_path}")
        frame = pd.read_parquet(file_path)
        frame["date"] = pd.to_datetime(frame["date"], utc=False)
        outputs[hypothesis_id] = frame.sort_values("date").reset_index(drop=True)
    return outputs


def write_decision_artifacts(
    leaderboard: pd.DataFrame,
    current_signals: pd.DataFrame,
    current_recommendation: dict,
    decision_report: dict,
    output_dir: str | Path | None = None,
) -> Path:
    out_dir = Path(output_dir or decision_output_dir())
    out_dir.mkdir(parents=True, exist_ok=True)

    leaderboard.to_parquet(out_dir / "leaderboard.parquet", index=False)
    leaderboard.to_csv(out_dir / "leaderboard.csv", index=False)
    (out_dir / "leaderboard.json").write_text(
        leaderboard.to_json(orient="records", date_format="iso", indent=2),
        encoding="utf-8",
    )

    current_signals.to_parquet(out_dir / "current_signals.parquet", index=False)
    current_signals.to_csv(out_dir / "current_signals.csv", index=False)

    (out_dir / "current_recommendation.json").write_text(
        json.dumps(current_recommendation, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (out_dir / "decision_report.json").write_text(
        json.dumps(decision_report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return out_dir
