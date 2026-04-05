from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class Hypothesis(ABC):
    name: str

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> pd.Series:
        raise NotImplementedError
