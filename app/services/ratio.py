from dataclasses import dataclass

from app.services.signals import classify_ratio


@dataclass(slots=True)
class RatioResult:
    ratio: float
    status: str


def calculate_gold_silver_ratio(gold_price_per_ounce: float, silver_price_per_ounce: float) -> RatioResult:
    if gold_price_per_ounce <= 0 or silver_price_per_ounce <= 0:
        raise ValueError("Prices must be positive.")

    ratio = gold_price_per_ounce / silver_price_per_ounce
    return RatioResult(ratio=round(ratio, 2), status=classify_ratio(ratio))
