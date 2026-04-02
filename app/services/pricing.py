from dataclasses import dataclass


@dataclass(slots=True)
class PurchaseComparisonResult:
    gold_acquisition_value: float
    silver_net_value: float
    silver_total_cost: float
    silver_vat_amount: float
    silver_required_appreciation_pct: float
    gold_future_value: float
    silver_future_value: float
    absolute_difference: float
    percentage_difference: float


def calculate_purchase_comparison(
    *,
    gold_purchase_amount: float,
    silver_purchase_amount: float,
    silver_vat_rate_pct: float = 19.0,
    future_price_change_pct: float = 0.0,
    purchase_premium_pct: float = 0.0,
    sale_discount_pct: float = 0.0,
) -> PurchaseComparisonResult:
    if gold_purchase_amount <= 0 or silver_purchase_amount <= 0:
        raise ValueError("Purchase amounts must be positive.")
    if silver_vat_rate_pct < 0 or silver_vat_rate_pct > 100:
        raise ValueError("Silver VAT rate must be between 0 and 100.")
    if purchase_premium_pct < 0:
        raise ValueError("Purchase premium cannot be negative.")
    if sale_discount_pct < 0 or sale_discount_pct >= 100:
        raise ValueError("Sale discount must be between 0 and 100.")

    premium_multiplier = 1 + purchase_premium_pct / 100
    discount_multiplier = 1 - sale_discount_pct / 100
    future_multiplier = 1 + future_price_change_pct / 100
    vat_multiplier = 1 + silver_vat_rate_pct / 100

    gold_acquisition_value = gold_purchase_amount * premium_multiplier
    silver_net_value = silver_purchase_amount
    silver_total_cost = silver_net_value * vat_multiplier * premium_multiplier
    silver_vat_amount = silver_net_value * (silver_vat_rate_pct / 100)

    gold_future_value = gold_purchase_amount * future_multiplier * discount_multiplier
    silver_future_value = silver_net_value * future_multiplier * discount_multiplier
    absolute_difference = silver_future_value - gold_future_value
    percentage_difference = (
        (absolute_difference / gold_future_value) * 100 if gold_future_value else 0.0
    )

    return PurchaseComparisonResult(
        gold_acquisition_value=round(gold_acquisition_value, 2),
        silver_net_value=round(silver_net_value, 2),
        silver_total_cost=round(silver_total_cost, 2),
        silver_vat_amount=round(silver_vat_amount, 2),
        silver_required_appreciation_pct=round(silver_vat_rate_pct, 2),
        gold_future_value=round(gold_future_value, 2),
        silver_future_value=round(silver_future_value, 2),
        absolute_difference=round(absolute_difference, 2),
        percentage_difference=round(percentage_difference, 2),
    )
