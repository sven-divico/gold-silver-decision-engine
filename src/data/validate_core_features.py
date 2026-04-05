from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pandas as pd


CRITICAL_COLUMNS = ("gold_close", "silver_close", "gsr")
EXPECTED_LEADING_NULLS = {
    "gold_ret_1d": 1,
    "silver_ret_1d": 1,
    "gsr_ret_1d": 1,
    "gold_mom_20d": 20,
    "silver_mom_20d": 20,
    "gsr_mom_20d": 20,
    "mom_divergence_20d": 20,
    "gsr_mean_252d": 251,
    "gsr_std_252d": 251,
    "gsr_z_252d": 251,
}


def validate_core_dataset(df: pd.DataFrame, metadata: dict | None = None) -> dict:
    metadata = metadata or {}
    if df.empty:
        raise ValueError("Merged core dataset is empty.")

    report = {
        "validation_status": "passed",
        "schema_checks": _schema_checks(df, metadata),
        "row_integrity_checks": _row_integrity_checks(df),
        "missing_data_checks": _missing_data_checks(df),
        "range_sanity_checks": _range_sanity_checks(df),
        "merge_diagnostics": dict(metadata.get("merge_diagnostics", {})),
    }

    _raise_for_validation_failures(report)
    return report


def write_validation_report(report: dict, path: str | Path) -> None:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")


def _schema_checks(df: pd.DataFrame, metadata: dict) -> dict:
    input_files = metadata.get("input_files", {})
    required_columns_present = all(column in df.columns for column in CRITICAL_COLUMNS)
    return {
        "input_file_exists": {
            asset: bool(details.get("exists"))
            for asset, details in input_files.items()
        },
        "required_columns_found": required_columns_present,
        "close_columns_numeric": {
            column: bool(pd.api.types.is_numeric_dtype(df[column]))
            for column in ("gold_close", "silver_close")
            if column in df.columns
        },
    }


def _row_integrity_checks(df: pd.DataFrame) -> dict:
    duplicate_dates = int(df["date"].duplicated().sum())
    sorted_ascending = bool(df["date"].is_monotonic_increasing)
    non_positive_close_rows = {
        column: int((df[column] <= 0).sum())
        for column in ("gold_close", "silver_close")
    }
    derived_columns = [column for column in df.columns if column not in ("date", "gold_close", "silver_close")]
    derived_values = df[derived_columns].to_numpy(dtype=float, copy=True) if derived_columns else np.empty((len(df), 0))
    infinite_values = int(np.isinf(derived_values).sum())
    return {
        "duplicate_dates": duplicate_dates,
        "sorted_ascending": sorted_ascending,
        "non_positive_close_rows": non_positive_close_rows,
        "infinite_values_in_derived_features": infinite_values,
    }


def _missing_data_checks(df: pd.DataFrame) -> dict:
    missing_by_column = {column: int(df[column].isna().sum()) for column in df.columns}
    unexplained_missing_by_column = {
        column: _unexpected_missing_count(df[column], EXPECTED_LEADING_NULLS.get(column, 0))
        for column in df.columns
    }
    unexplained_missing_ratio_critical = {
        column: _unexpected_missing_ratio(df[column], EXPECTED_LEADING_NULLS.get(column, 0))
        for column in CRITICAL_COLUMNS
    }
    return {
        "missing_by_column": missing_by_column,
        "unexpected_missing_by_column": unexplained_missing_by_column,
        "has_unexpected_missing_values": any(count > 0 for count in unexplained_missing_by_column.values()),
        "critical_columns_unexpected_missing_ratio": unexplained_missing_ratio_critical,
    }


def _range_sanity_checks(df: pd.DataFrame) -> dict:
    return {
        "daily_return_abs_gt_20pct": {
            column: int(df[column].abs().gt(0.20).sum())
            for column in ("gold_ret_1d", "silver_ret_1d", "gsr_ret_1d")
            if column in df.columns
        },
        "gsr_outside_10_200": int((df["gsr"].lt(10) | df["gsr"].gt(200)).sum()),
    }


def _raise_for_validation_failures(report: dict) -> None:
    schema_checks = report["schema_checks"]
    if not schema_checks["required_columns_found"]:
        raise ValueError("Final dataframe is missing one or more critical columns.")
    if not all(schema_checks["input_file_exists"].values()):
        raise FileNotFoundError("One or more required input files are missing.")
    if not all(schema_checks["close_columns_numeric"].values()):
        raise ValueError("One or more close columns are not numeric.")

    row_checks = report["row_integrity_checks"]
    if row_checks["duplicate_dates"] > 0:
        raise ValueError("Duplicate dates remain in the final dataframe.")
    if not row_checks["sorted_ascending"]:
        raise ValueError("Final dataframe is not sorted ascending by date.")
    if any(count > 0 for count in row_checks["non_positive_close_rows"].values()):
        raise ValueError("Final dataframe contains zero or negative close prices.")
    if row_checks["infinite_values_in_derived_features"] > 0:
        raise ValueError("Final dataframe contains infinite values in derived features.")

    critical_missing_ratio = report["missing_data_checks"]["critical_columns_unexpected_missing_ratio"]
    if any(ratio > 0.05 for ratio in critical_missing_ratio.values()):
        raise ValueError("More than 5% of non-lookback rows have unexplained missing values in critical columns.")


def _unexpected_missing_count(series: pd.Series, allowed_leading_nulls: int) -> int:
    if series.empty:
        return 0
    unexpected = series.iloc[allowed_leading_nulls:]
    return int(unexpected.isna().sum())


def _unexpected_missing_ratio(series: pd.Series, allowed_leading_nulls: int) -> float:
    if series.empty:
        return 0.0
    relevant = series.iloc[allowed_leading_nulls:]
    if relevant.empty:
        return 0.0
    return float(relevant.isna().sum() / len(relevant))
