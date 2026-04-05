from __future__ import annotations

import numpy as np
import pandas as pd


FORWARD_WINDOW_DAYS = 20


def compute_forward_return(df: pd.DataFrame, window_days: int = FORWARD_WINDOW_DAYS) -> pd.Series:
    return (df["gsr"].shift(-window_days) / df["gsr"]) - 1.0


def classify_regime(df: pd.DataFrame) -> pd.DataFrame:
    gsr_vol_20d = df["gsr_ret_1d"].rolling(20).std()
    trailing_median = gsr_vol_20d.expanding().median().shift(1)
    regime = np.where(gsr_vol_20d > trailing_median, "STRESS", "NORMAL")
    regime = pd.Series(regime, index=df.index, name="regime")
    return pd.DataFrame(
        {
            "gsr_vol_20d": gsr_vol_20d,
            "gsr_vol_20d_trailing_median": trailing_median,
            "regime": regime,
        },
        index=df.index,
    )


def apply_regime_filter(df: pd.DataFrame, hypothesis_name: str) -> pd.Series:
    if hypothesis_name == "h1_mean_reversion":
        active = df["regime"] == "NORMAL"
    elif hypothesis_name == "h2_gold_lead":
        # "Early trend" is represented as non-stress momentum pickup in the ratio.
        early_trend = (df["gsr_mom_20d"].abs() >= 0.01) & (df["regime"] == "NORMAL")
        active = (df["regime"] == "NORMAL") | early_trend
    elif hypothesis_name == "h3_momentum":
        # "Transition" is represented as days immediately after a regime flip.
        transition = df["regime"] != df["regime"].shift(1)
        active = (df["regime"] == "STRESS") | transition.fillna(False)
    else:
        raise ValueError(f"Unknown hypothesis name: {hypothesis_name}")
    return active.fillna(False)


def build_hypothesis_result(df: pd.DataFrame, raw_signal: pd.Series, hypothesis_name: str) -> pd.DataFrame:
    regime_frame = classify_regime(df)
    active = apply_regime_filter(
        pd.DataFrame(
            {
                "regime": regime_frame["regime"],
                "gsr_mom_20d": df["gsr_mom_20d"],
            },
            index=df.index,
        ),
        hypothesis_name=hypothesis_name,
    )

    signal = raw_signal.where(active, 0).astype(int)
    forward_return = compute_forward_return(df)
    pnl = signal * (-forward_return)

    return pd.DataFrame(
        {
            "date": df["date"],
            "signal": signal,
            "regime": regime_frame["regime"],
            "active": active.astype(bool),
            "forward_return": forward_return,
            "pnl": pnl,
        },
        index=df.index,
    )
