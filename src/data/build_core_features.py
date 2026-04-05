from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.load_prices import load_gold_prices, load_silver_prices
from src.data.validate_core_features import validate_core_dataset, write_validation_report
from src.utils.paths import gold_import_path, processed_data_dir, silver_import_path


REQUIRED_OUTPUT_COLUMNS = [
    "date",
    "gold_close",
    "silver_close",
    "gsr",
    "gold_ret_1d",
    "silver_ret_1d",
    "gsr_ret_1d",
    "gold_mom_20d",
    "silver_mom_20d",
    "gsr_mom_20d",
    "mom_divergence_20d",
    "gsr_mean_252d",
    "gsr_std_252d",
    "gsr_z_252d",
]


def merge_price_series(gold_df: pd.DataFrame, silver_df: pd.DataFrame) -> pd.DataFrame:
    merged = pd.merge(gold_df, silver_df, on="date", how="inner", sort=True)
    merged = merged.sort_values("date").reset_index(drop=True)
    if merged.empty:
        raise ValueError("Merged core dataset is empty.")
    return merged


def add_core_features(df: pd.DataFrame) -> pd.DataFrame:
    featured = df.copy()
    featured["gsr"] = featured["gold_close"] / featured["silver_close"]
    featured["gold_ret_1d"] = featured["gold_close"].pct_change(1)
    featured["silver_ret_1d"] = featured["silver_close"].pct_change(1)
    featured["gsr_ret_1d"] = featured["gsr"].pct_change(1)

    featured["gold_mom_20d"] = featured["gold_close"] / featured["gold_close"].shift(20) - 1
    featured["silver_mom_20d"] = featured["silver_close"] / featured["silver_close"].shift(20) - 1
    featured["gsr_mom_20d"] = featured["gsr"] / featured["gsr"].shift(20) - 1
    featured["mom_divergence_20d"] = featured["gold_mom_20d"] - featured["silver_mom_20d"]

    featured["gsr_mean_252d"] = featured["gsr"].rolling(252).mean()
    featured["gsr_std_252d"] = featured["gsr"].rolling(252).std()
    featured["gsr_z_252d"] = (featured["gsr"] - featured["gsr_mean_252d"]) / featured["gsr_std_252d"]
    return featured


def build_core_dataset(
    gold_path: str | Path | None = None,
    silver_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> tuple[pd.DataFrame, dict]:
    gold_path = Path(gold_path or gold_import_path())
    silver_path = Path(silver_path or silver_import_path())
    output_dir = Path(output_dir or processed_data_dir())

    gold_df = load_gold_prices(gold_path)
    silver_df = load_silver_prices(silver_path)
    merged = merge_price_series(gold_df, silver_df)
    featured = add_core_features(merged)

    metadata = _build_metadata(gold_df, silver_df, featured, gold_path, silver_path)
    report = validate_core_dataset(featured, metadata)
    save_core_dataset(featured, report, output_dir=output_dir)
    return featured, report


def save_core_dataset(df: pd.DataFrame, report: dict, *, output_dir: str | Path) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    parquet_path = output_path / "core_features.parquet"
    csv_path = output_path / "core_features.csv"
    report_path = output_path / "core_features_report.json"

    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False)
    write_validation_report(report, report_path)


def _build_metadata(
    gold_df: pd.DataFrame,
    silver_df: pd.DataFrame,
    featured: pd.DataFrame,
    gold_path: Path,
    silver_path: Path,
) -> dict:
    gold_meta = dict(gold_df.attrs.get("source_metadata", {}))
    silver_meta = dict(silver_df.attrs.get("source_metadata", {}))
    return {
        "input_files": {
            "gold": {
                "exists": gold_path.exists(),
                "path": str(gold_path),
                "original_rows": gold_meta.get("original_rows", len(gold_df)),
                "normalized_rows": gold_meta.get("normalized_rows", len(gold_df)),
                "date_min": gold_meta.get("date_min"),
                "date_max": gold_meta.get("date_max"),
            },
            "silver": {
                "exists": silver_path.exists(),
                "path": str(silver_path),
                "original_rows": silver_meta.get("original_rows", len(silver_df)),
                "normalized_rows": silver_meta.get("normalized_rows", len(silver_df)),
                "date_min": silver_meta.get("date_min"),
                "date_max": silver_meta.get("date_max"),
            },
        },
        "merge_diagnostics": {
            "original_gold_rows": int(gold_meta.get("original_rows", len(gold_df))),
            "original_silver_rows": int(silver_meta.get("original_rows", len(silver_df))),
            "overlapping_merged_rows": int(len(featured)),
            "rows_removed_due_to_date_mismatch": int((len(gold_df) + len(silver_df)) - (2 * len(featured))),
            "gold_date_min": gold_meta.get("date_min"),
            "gold_date_max": gold_meta.get("date_max"),
            "silver_date_min": silver_meta.get("date_min"),
            "silver_date_max": silver_meta.get("date_max"),
            "merged_date_min": featured["date"].min().date().isoformat(),
            "merged_date_max": featured["date"].max().date().isoformat(),
        },
    }


def main() -> None:
    dataset, report = build_core_dataset()
    diagnostics = report["merge_diagnostics"]
    print(f"Loaded gold rows: {diagnostics['original_gold_rows']}")
    print(f"Loaded silver rows: {diagnostics['original_silver_rows']}")
    print(f"Merged rows: {diagnostics['overlapping_merged_rows']}")
    print(f"Date range: {diagnostics['merged_date_min']} to {diagnostics['merged_date_max']}")
    print(f"Validation: {report['validation_status'].upper()}")
    output_path = processed_data_dir()
    print(f"Saved: {output_path / 'core_features.parquet'}")
    print(f"Saved: {output_path / 'core_features.csv'}")
    print(f"Saved: {output_path / 'core_features_report.json'}")


if __name__ == "__main__":
    main()
