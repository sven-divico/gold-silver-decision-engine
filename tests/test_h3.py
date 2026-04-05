from __future__ import annotations

import pandas as pd

from src.hypotheses.h3_momentum import H3Momentum


def test_h3_generates_expected_signals() -> None:
    frame = pd.DataFrame({"gsr_mom_20d": [0.04, 0.01, -0.04, -0.01]})

    signal = H3Momentum(threshold=0.03).generate_signal(frame)

    assert signal.tolist() == [1, 0, -1, 0]
