from __future__ import annotations

import numpy as np
import pandas as pd

from src.hypotheses.base import Hypothesis


class H3Momentum(Hypothesis):
    name = "h3_momentum"

    def __init__(self, threshold: float = 0.03) -> None:
        self.threshold = threshold

    def generate_signal(self, df: pd.DataFrame) -> pd.Series:
        signal = np.zeros(len(df), dtype=int)
        signal[df["gsr_mom_20d"] > self.threshold] = 1
        signal[df["gsr_mom_20d"] < -self.threshold] = -1
        return pd.Series(signal, index=df.index, name="signal")
