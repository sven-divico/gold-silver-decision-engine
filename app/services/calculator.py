from dataclasses import dataclass

from app.services.pricing import PurchaseComparisonResult, calculate_purchase_comparison
from app.services.ratio import RatioResult, calculate_gold_silver_ratio
from app.services.signals import ratio_signal_text


@dataclass(slots=True)
class CalculatorInputs:
    gold_purchase_amount: float
    silver_purchase_amount: float
    silver_vat_rate_pct: float
    future_price_change_pct: float
    gold_price_per_ounce: float
    silver_price_per_ounce: float
    purchase_premium_pct: float = 0.0
    sale_discount_pct: float = 0.0
    holding_period_years: float = 0.0


@dataclass(slots=True)
class CalculatorResult:
    gold_value: float
    silver_net_value: float
    silver_vat_amount: float
    silver_total_cost: float
    required_appreciation_pct: float
    gold_future_value: float
    silver_future_value: float
    future_price_change_pct: float
    absolute_difference: float
    percentage_difference: float
    ratio: float
    ratio_status: str
    ratio_signal: str
    assumptions: list[str]


DEFAULT_ASSUMPTIONS = [
    "No buy or sell spread is considered in this calculator.",
    "No VAT recovery is assumed on a private silver sale.",
    "Ratio status thresholds are heuristic only and not predictive signals.",
    "This is an analytical tool and not investment advice.",
]


def calculate_decision(inputs: CalculatorInputs) -> CalculatorResult:
    if inputs.holding_period_years < 0:
        raise ValueError("Holding period cannot be negative.")

    purchase_result: PurchaseComparisonResult = calculate_purchase_comparison(
        gold_purchase_amount=inputs.gold_purchase_amount,
        silver_purchase_amount=inputs.silver_purchase_amount,
        silver_vat_rate_pct=inputs.silver_vat_rate_pct,
        future_price_change_pct=inputs.future_price_change_pct,
        purchase_premium_pct=inputs.purchase_premium_pct,
        sale_discount_pct=inputs.sale_discount_pct,
    )
    ratio_result: RatioResult = calculate_gold_silver_ratio(
        gold_price_per_ounce=inputs.gold_price_per_ounce,
        silver_price_per_ounce=inputs.silver_price_per_ounce,
    )

    return CalculatorResult(
        gold_value=purchase_result.gold_acquisition_value,
        silver_net_value=purchase_result.silver_net_value,
        silver_vat_amount=purchase_result.silver_vat_amount,
        silver_total_cost=purchase_result.silver_total_cost,
        required_appreciation_pct=purchase_result.silver_required_appreciation_pct,
        gold_future_value=purchase_result.gold_future_value,
        silver_future_value=purchase_result.silver_future_value,
        future_price_change_pct=round(inputs.future_price_change_pct, 2),
        absolute_difference=purchase_result.absolute_difference,
        percentage_difference=purchase_result.percentage_difference,
        ratio=ratio_result.ratio,
        ratio_status=ratio_result.status,
        ratio_signal=ratio_signal_text(ratio_result),
        assumptions=DEFAULT_ASSUMPTIONS.copy(),
    )
