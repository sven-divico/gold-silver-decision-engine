from __future__ import annotations

import pandas as pd
import pytest

from src.hypotheses.backtest import build_hypothesis_result, classify_regime, compute_forward_return


def test_forward_return_is_aligned_to_future_window() -> None:
    frame = pd.DataFrame({"gsr": [float(value) for value in range(100, 131)]})

    forward = compute_forward_return(frame, window_days=20)

    assert forward.iloc[0] == pytest.approx((120.0 / 100.0) - 1.0)
    assert pd.isna(forward.iloc[-1])


def test_h1_regime_filter_disables_signal_in_stress() -> None:
    frame = _base_backtest_frame()
    frame.loc[25, "gsr_ret_1d"] = 0.30
    raw_signal = pd.Series([1] * len(frame))

    result = build_hypothesis_result(frame, raw_signal, hypothesis_name="h1_mean_reversion")

    assert result.loc[25, "regime"] == "STRESS"
    assert bool(result.loc[25, "active"]) is False
    assert result.loc[25, "signal"] == 0


def test_pnl_uses_negative_forward_return_for_long_signal() -> None:
    frame = _base_backtest_frame()
    frame["gsr"] = [100.0 - (0.2 * idx) for idx in range(len(frame))]
    raw_signal = pd.Series([1] * len(frame))

    result = build_hypothesis_result(frame, raw_signal, hypothesis_name="h1_mean_reversion")

    first_trade_index = int(result.index[result["signal"] != 0][0])
    assert result.loc[first_trade_index, "forward_return"] < 0
    assert result.loc[first_trade_index, "pnl"] > 0


def test_regime_classification_has_no_lookahead_bias() -> None:
    base = _base_backtest_frame()
    shocked = base.copy()
    shocked.loc[35:, "gsr_ret_1d"] = [0.35, -0.25, 0.30, -0.20, 0.40]

    base_regime = classify_regime(base)
    shocked_regime = classify_regime(shocked)

    assert base_regime["regime"].iloc[:35].tolist() == shocked_regime["regime"].iloc[:35].tolist()


def _base_backtest_frame() -> pd.DataFrame:
    periods = 40
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=periods, freq="D"),
            "gsr": [80.0 + (0.1 * idx) for idx in range(periods)],
            "gsr_z_252d": [0.0] * periods,
            "gsr_mom_20d": [0.02] * periods,
            "gold_mom_20d": [0.03] * periods,
            "silver_mom_20d": [0.01] * periods,
            "gsr_ret_1d": [0.01] * periods,
        }
    )
