from __future__ import annotations

import numpy as np
import pandas as pd

from src.hypotheses.base import Hypothesis


class H2GoldLead(Hypothesis):
    name = "h2_gold_lead"

    def __init__(self, threshold: float = 0.03) -> None:
        self.threshold = threshold

    def generate_signal(self, df: pd.DataFrame) -> pd.Series:
        signal = np.zeros(len(df), dtype=int)
        long_condition = (df["gold_mom_20d"] > self.threshold) & (
            df["silver_mom_20d"] < (df["gold_mom_20d"] * 0.5)
        )
        short_condition = (df["silver_mom_20d"] > self.threshold) & (
            df["gold_mom_20d"] < (df["silver_mom_20d"] * 0.5)
        )
        signal[long_condition] = 1
        signal[short_condition] = -1
        return pd.Series(signal, index=df.index, name="signal")
