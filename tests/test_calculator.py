import pytest

from app.services.calculator import CalculatorInputs, calculate_decision


def test_calculate_decision_returns_unified_result() -> None:
    result = calculate_decision(
        CalculatorInputs(
            gold_purchase_amount=1000,
            silver_purchase_amount=1000,
            silver_vat_rate_pct=19,
            future_price_change_pct=10,
            gold_price_per_ounce=3000,
            silver_price_per_ounce=30,
        )
    )

    assert result.gold_value == 1000
    assert result.silver_net_value == 1000
    assert result.silver_vat_amount == 190
    assert result.silver_total_cost == 1190
    assert result.required_appreciation_pct == 19
    assert result.ratio == 100
    assert result.ratio_status == "elevated"
    assert "not investment advice" in " ".join(result.assumptions).lower()


def test_calculate_decision_rejects_negative_holding_period() -> None:
    with pytest.raises(ValueError):
        calculate_decision(
            CalculatorInputs(
                gold_purchase_amount=1000,
                silver_purchase_amount=1000,
                silver_vat_rate_pct=19,
                future_price_change_pct=0,
                gold_price_per_ounce=3000,
                silver_price_per_ounce=30,
                holding_period_years=-1,
            )
        )
