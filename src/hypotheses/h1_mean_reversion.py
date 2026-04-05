from __future__ import annotations

import numpy as np
import pandas as pd

from src.hypotheses.base import Hypothesis


class H1MeanReversion(Hypothesis):
    name = "h1_mean_reversion"

    def generate_signal(self, df: pd.DataFrame) -> pd.Series:
        signal = np.zeros(len(df), dtype=int)
        signal[df["gsr_z_252d"] > 2.0] = 1
        signal[df["gsr_z_252d"] < -2.0] = -1
        return pd.Series(signal, index=df.index, name="signal")
