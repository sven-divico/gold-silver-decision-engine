from __future__ import annotations

import pandas as pd

from src.hypotheses.h2_gold_lead import H2GoldLead


def test_h2_generates_expected_signals() -> None:
    frame = pd.DataFrame(
        {
            "gold_mom_20d": [0.04, 0.01, 0.01, 0.00],
            "silver_mom_20d": [0.01, 0.05, 0.03, 0.00],
        }
    )

    signal = H2GoldLead(threshold=0.03).generate_signal(frame)

    assert signal.tolist() == [1, -1, 0, 0]
