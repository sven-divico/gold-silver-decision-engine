import pytest

from app.services.ratio import calculate_gold_silver_ratio
from app.services.signals import classify_ratio


def test_calculate_gold_silver_ratio_classifies_elevated() -> None:
    result = calculate_gold_silver_ratio(3200, 35)

    assert result.ratio == pytest.approx(91.43, rel=1e-3)
    assert result.status == "elevated"


def test_classify_ratio_thresholds() -> None:
    assert classify_ratio(59.99) == "compressed"
    assert classify_ratio(60) == "neutral"
    assert classify_ratio(80) == "neutral"
    assert classify_ratio(80.01) == "elevated"


def test_calculate_gold_silver_ratio_rejects_invalid_prices() -> None:
    with pytest.raises(ValueError):
        calculate_gold_silver_ratio(3000, 0)
