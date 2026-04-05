from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.data.load_prices import load_gold_prices, normalize_price_frame


def test_loads_valid_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "xauusd_d.csv"
    csv_path.write_text("Date,Close\n2024-01-02,2050\n2024-01-03,2060\n", encoding="utf-8")

    frame = load_gold_prices(csv_path)

    assert list(frame.columns) == ["date", "gold_close"]
    assert frame["gold_close"].tolist() == [2050.0, 2060.0]
    assert frame["date"].dt.strftime("%Y-%m-%d").tolist() == ["2024-01-02", "2024-01-03"]


def test_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Missing input file"):
        load_gold_prices(tmp_path / "missing.csv")


def test_rejects_missing_required_columns() -> None:
    frame = pd.DataFrame({"Date": ["2024-01-02"], "Open": [2050]})

    with pytest.raises(ValueError, match="missing required column: close"):
        normalize_price_frame(frame, asset_name="gold")


def test_removes_duplicate_dates_keeping_last_occurrence() -> None:
    frame = pd.DataFrame(
        {
            "Date": ["2024-01-02", "2024-01-02", "2024-01-03"],
            "Close": [2050, 2075, 2060],
        }
    )

    normalized = normalize_price_frame(frame, asset_name="gold")

    assert normalized["date"].dt.strftime("%Y-%m-%d").tolist() == ["2024-01-02", "2024-01-03"]
    assert normalized["gold_close"].tolist() == [2075.0, 2060.0]


def test_sorts_dates_ascending() -> None:
    frame = pd.DataFrame(
        {
            "Date": ["2024-01-03", "2024-01-02"],
            "Close": [2060, 2050],
        }
    )

    normalized = normalize_price_frame(frame, asset_name="gold")

    assert normalized["date"].dt.strftime("%Y-%m-%d").tolist() == ["2024-01-02", "2024-01-03"]
