from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.hypotheses.backtest import build_hypothesis_result
from src.hypotheses.h1_mean_reversion import H1MeanReversion
from src.hypotheses.h2_gold_lead import H2GoldLead
from src.hypotheses.h3_momentum import H3Momentum
from src.hypotheses.metrics import compute_performance_metrics
from src.utils.paths import processed_data_dir, project_root


INPUT_FILE = "core_features.parquet"
REQUIRED_COLUMNS = (
    "date",
    "gsr",
    "gsr_z_252d",
    "gsr_mom_20d",
    "gold_mom_20d",
    "silver_mom_20d",
    "gsr_ret_1d",
)


def run_hypothesis_engine(
    input_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, dict[str, float | int]]:
    dataset = load_dataset(input_path)
    output_path = Path(output_dir or (project_root() / "data" / "hypotheses"))
    output_path.mkdir(parents=True, exist_ok=True)

    print(
        f"Loaded dataset: {dataset['date'].min().date().isoformat()} -> "
        f"{dataset['date'].max().date().isoformat()}"
    )

    hypotheses = [H1MeanReversion(), H2GoldLead(), H3Momentum()]
    summary: dict[str, dict[str, float | int]] = {}

    for hypothesis in hypotheses:
        print(f"Running {hypothesis.name.upper()}...")
        raw_signal = hypothesis.generate_signal(dataset)
        result = build_hypothesis_result(dataset, raw_signal, hypothesis.name)
        summary[hypothesis.name] = compute_performance_metrics(result)
        result.to_parquet(output_path / f"{hypothesis.name}.parquet", index=False)

    summary_path = output_path / "performance_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print("\nBacktest complete.\n")
    for name, metrics in summary.items():
        print(f"{name.upper()} return: {metrics['total_return']:.2f} | hit rate: {metrics['hit_rate']:.2f}")
    print(f"\nSaved results to {output_path}")
    return summary


def load_dataset(input_path: str | Path | None = None) -> pd.DataFrame:
    dataset_path = Path(input_path or (processed_data_dir() / INPUT_FILE))
    if not dataset_path.exists():
        raise FileNotFoundError(f"Missing processed dataset: {dataset_path}")
    df = pd.read_parquet(dataset_path)

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns in dataset: {', '.join(missing_columns)}")

    loaded = df.loc[:, list(REQUIRED_COLUMNS)].copy()
    loaded["date"] = pd.to_datetime(loaded["date"], utc=False)
    loaded = loaded.sort_values("date").reset_index(drop=True)
    return loaded


def main() -> None:
    run_hypothesis_engine()


if __name__ == "__main__":
    main()
