import pytest

from app.services.pricing import calculate_purchase_comparison


def test_calculate_purchase_comparison_uses_vat_as_sunk_cost() -> None:
    result = calculate_purchase_comparison(
        gold_purchase_amount=1000,
        silver_purchase_amount=1000,
        silver_vat_rate_pct=19,
        future_price_change_pct=10,
    )

    assert result.gold_acquisition_value == 1000
    assert result.silver_total_cost == 1190
    assert result.silver_vat_amount == 190
    assert result.silver_required_appreciation_pct == 19
    assert result.gold_future_value == 1100
    assert result.silver_future_value == 1100


def test_calculate_purchase_comparison_rejects_non_positive_purchase_amounts() -> None:
    with pytest.raises(ValueError):
        calculate_purchase_comparison(gold_purchase_amount=0, silver_purchase_amount=1000)


def test_calculate_purchase_comparison_rejects_invalid_percentage_inputs() -> None:
    with pytest.raises(ValueError):
        calculate_purchase_comparison(
            gold_purchase_amount=1000,
            silver_purchase_amount=1000,
            silver_vat_rate_pct=101,
        )

    with pytest.raises(ValueError):
        calculate_purchase_comparison(
            gold_purchase_amount=1000,
            silver_purchase_amount=1000,
            sale_discount_pct=100,
        )
