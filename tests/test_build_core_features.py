from __future__ import annotations

import math

import pandas as pd
import pytest

from src.data.build_core_features import add_core_features, merge_price_series


def test_computes_gsr_correctly() -> None:
    frame = _feature_input([2000, 2100], [25, 30])

    featured = add_core_features(frame)

    assert featured["gsr"].tolist() == [80.0, 70.0]


def test_computes_returns_correctly() -> None:
    frame = _feature_input([2000, 2200], [25, 20])

    featured = add_core_features(frame)

    assert math.isnan(featured.loc[0, "gold_ret_1d"])
    assert featured.loc[1, "gold_ret_1d"] == pytest.approx(0.10)
    assert featured.loc[1, "silver_ret_1d"] == pytest.approx(-0.20)
    assert featured.loc[1, "gsr_ret_1d"] == pytest.approx(0.375)


def test_computes_momentum_correctly() -> None:
    gold = list(range(100, 121)) + [132]
    silver = list(range(50, 71)) + [66]
    frame = _feature_input(gold, silver)

    featured = add_core_features(frame)

    assert math.isnan(featured.loc[19, "gold_mom_20d"])
    assert featured.loc[20, "gold_mom_20d"] == pytest.approx(20 / 100)
    assert featured.loc[20, "silver_mom_20d"] == pytest.approx(20 / 50)
    assert featured.loc[20, "mom_divergence_20d"] == pytest.approx((20 / 100) - (20 / 50))


def test_computes_rolling_z_score_correctly() -> None:
    gold = [100 + value for value in range(253)]
    silver = [2.0] * 253
    frame = _feature_input(gold, silver)

    featured = add_core_features(frame)
    expected_gsr = pd.Series(gold, dtype=float) / pd.Series(silver, dtype=float)
    expected_mean = expected_gsr.iloc[1:253].mean()
    expected_std = expected_gsr.iloc[1:253].std()
    expected_z = (expected_gsr.iloc[252] - expected_mean) / expected_std

    assert math.isnan(featured.loc[250, "gsr_z_252d"])
    assert featured.loc[252, "gsr_mean_252d"] == pytest.approx(expected_mean)
    assert featured.loc[252, "gsr_std_252d"] == pytest.approx(expected_std)
    assert featured.loc[252, "gsr_z_252d"] == pytest.approx(expected_z)


def test_inner_join_drops_non_overlapping_dates_correctly() -> None:
    gold = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "gold_close": [2000.0, 2010.0, 2020.0],
        }
    )
    silver = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
            "silver_close": [25.0, 25.5, 26.0],
        }
    )

    merged = merge_price_series(gold, silver)

    assert merged["date"].dt.strftime("%Y-%m-%d").tolist() == ["2024-01-02", "2024-01-03"]


def _feature_input(gold_close: list[float], silver_close: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=len(gold_close), freq="D"),
            "gold_close": pd.Series(gold_close, dtype=float),
            "silver_close": pd.Series(silver_close, dtype=float),
        }
    )
