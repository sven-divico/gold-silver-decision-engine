from __future__ import annotations

import math

import pandas as pd


def compute_performance_metrics(result_df: pd.DataFrame) -> dict[str, float | int]:
    tradable = result_df[result_df["signal"] != 0].copy()
    tradable = tradable[tradable["forward_return"].notna()]

    pnl = tradable["pnl"] if not tradable.empty else pd.Series(dtype=float)
    total_return = float(pnl.sum()) if not tradable.empty else 0.0
    average_pnl = float(pnl.mean()) if not tradable.empty else 0.0
    hit_rate = float((pnl > 0).mean()) if not tradable.empty else 0.0
    number_of_trades = int(len(tradable))
    max_drawdown = float(_max_drawdown(pnl))
    sharpe_ratio = float(_sharpe_ratio(pnl))

    return {
        "total_return": total_return,
        "hit_rate": hit_rate,
        "average_pnl": average_pnl,
        "max_drawdown": max_drawdown,
        "number_of_trades": number_of_trades,
        "sharpe_ratio": sharpe_ratio,
    }


def _max_drawdown(pnl: pd.Series) -> float:
    if pnl.empty:
        return 0.0
    equity_curve = pnl.cumsum()
    running_peak = equity_curve.cummax()
    drawdown = equity_curve - running_peak
    return float(drawdown.min())


def _sharpe_ratio(pnl: pd.Series) -> float:
    if pnl.empty:
        return 0.0
    std = float(pnl.std(ddof=0))
    if std == 0.0:
        return 0.0
    return float(math.sqrt(252) * pnl.mean() / std)
