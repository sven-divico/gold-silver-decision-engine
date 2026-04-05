from __future__ import annotations

import pandas as pd

from src.hypotheses.h1_mean_reversion import H1MeanReversion


def test_h1_generates_expected_signals() -> None:
    frame = pd.DataFrame({"gsr_z_252d": [2.5, 1.2, -2.1, -1.9]})

    signal = H1MeanReversion().generate_signal(frame)

    assert signal.tolist() == [1, 0, -1, 0]
