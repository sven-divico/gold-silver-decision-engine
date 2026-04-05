from __future__ import annotations

import pandas as pd
import pytest

from src.data.build_core_features import add_core_features
from src.data.validate_core_features import validate_core_dataset


def test_flags_negative_prices() -> None:
    frame = _base_featured_frame(260)
    frame.loc[10, "gold_close"] = -1.0
    frame = add_core_features(frame[["date", "gold_close", "silver_close"]])

    with pytest.raises(ValueError, match="zero or negative close prices"):
        validate_core_dataset(frame, _metadata())


def test_flags_empty_merged_dataset() -> None:
    with pytest.raises(ValueError, match="empty"):
        validate_core_dataset(pd.DataFrame(), _metadata())


def test_allows_expected_lookback_nulls() -> None:
    frame = add_core_features(_base_featured_frame(260))

    report = validate_core_dataset(frame, _metadata())

    assert report["validation_status"] == "passed"
    assert report["missing_data_checks"]["unexpected_missing_by_column"]["gsr_z_252d"] == 0


def test_rejects_unexplained_missing_values() -> None:
    frame = add_core_features(_base_featured_frame(260))
    frame.loc[:20, "gold_close"] = pd.NA
    frame["gsr"] = frame["gold_close"] / frame["silver_close"]

    with pytest.raises(ValueError, match="More than 5%"):
        validate_core_dataset(frame, _metadata())


def _base_featured_frame(length: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=length, freq="D"),
            "gold_close": pd.Series(range(100, 100 + length), dtype=float),
            "silver_close": pd.Series(range(50, 50 + length), dtype=float),
        }
    )


def _metadata() -> dict:
    return {
        "input_files": {
            "gold": {"exists": True},
            "silver": {"exists": True},
        },
        "merge_diagnostics": {},
    }
