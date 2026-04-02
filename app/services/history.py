from dataclasses import dataclass
from datetime import date
from statistics import mean

from app.repositories.prices import HistoricalPriceRepository, PricePoint
from app.services.signals import classify_ratio


@dataclass(slots=True)
class HistoricalAnalysisFilters:
    start_date: date | None = None
    end_date: date | None = None
    overlap_only: bool = False


@dataclass(slots=True)
class HistoricalRatioPoint:
    recorded_on: date
    gold_price_per_ounce_eur: float
    silver_price_per_ounce_eur: float
    ratio: float
    ratio_status: str


@dataclass(slots=True)
class HistoricalRatioSummary:
    latest_ratio: float
    min_ratio: float
    max_ratio: float
    average_ratio: float
    point_count: int
    effective_start_date: date | None
    effective_end_date: date | None


@dataclass(slots=True)
class HistoricalAnalysisMetadata:
    filters: HistoricalAnalysisFilters
    gold_row_count: int
    silver_row_count: int
    gold_distinct_dates: int
    silver_distinct_dates: int
    overlap_date_count: int
    effective_start_date: date | None
    effective_end_date: date | None
    note: str | None


@dataclass(slots=True)
class HistoricalRatioOverview:
    points: list[HistoricalRatioPoint]
    summary: HistoricalRatioSummary | None
    data_note: str
    metadata: HistoricalAnalysisMetadata


def align_price_histories(
    gold_history: list[PricePoint], silver_history: list[PricePoint]
) -> list[tuple[date, float, float]]:
    silver_by_date = {point.recorded_on: point.price_per_ounce_eur for point in silver_history}
    aligned = []
    for gold_point in gold_history:
        silver_price = silver_by_date.get(gold_point.recorded_on)
        if silver_price is None:
            continue
        aligned.append((gold_point.recorded_on, gold_point.price_per_ounce_eur, silver_price))
    return aligned


def deduplicate_price_history(history: list[PricePoint]) -> list[PricePoint]:
    deduped: dict[date, PricePoint] = {}
    for point in sorted(history, key=lambda item: (item.recorded_on, item.row_id or 0)):
        deduped.setdefault(point.recorded_on, point)
    return list(deduped.values())


def build_historical_ratio_points(
    aligned_prices: list[tuple[date, float, float]]
) -> list[HistoricalRatioPoint]:
    points = []
    for recorded_on, gold_price, silver_price in aligned_prices:
        if gold_price <= 0 or silver_price <= 0:
            raise ValueError("Historical prices must be positive.")
        ratio = round(gold_price / silver_price, 2)
        points.append(
            HistoricalRatioPoint(
                recorded_on=recorded_on,
                gold_price_per_ounce_eur=round(gold_price, 2),
                silver_price_per_ounce_eur=round(silver_price, 2),
                ratio=ratio,
                ratio_status=classify_ratio(ratio),
            )
        )
    return points


def summarize_historical_ratios(points: list[HistoricalRatioPoint]) -> HistoricalRatioSummary | None:
    if not points:
        return None

    ratios = [point.ratio for point in points]
    return HistoricalRatioSummary(
        latest_ratio=points[-1].ratio,
        min_ratio=min(ratios),
        max_ratio=max(ratios),
        average_ratio=round(mean(ratios), 2),
        point_count=len(points),
        effective_start_date=points[0].recorded_on,
        effective_end_date=points[-1].recorded_on,
    )


def get_historical_ratio_overview(
    repository: HistoricalPriceRepository,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    overlap_only: bool = False,
) -> HistoricalRatioOverview:
    if start_date and end_date and start_date > end_date:
        raise ValueError("Start date cannot be after end date.")

    filters = HistoricalAnalysisFilters(
        start_date=start_date,
        end_date=end_date,
        overlap_only=overlap_only,
    )
    prices = repository.get_prices_for_metals(
        ["gold", "silver"], start_date=start_date, end_date=end_date
    )
    gold_history = prices["gold"]
    silver_history = prices["silver"]
    if overlap_only:
        gold_history = deduplicate_price_history(gold_history)
        silver_history = deduplicate_price_history(silver_history)
    aligned = align_price_histories(gold_history, silver_history)
    points = build_historical_ratio_points(aligned)
    summary = summarize_historical_ratios(points)
    overlap_dates = {point.recorded_on for point in points}
    note = None
    if overlap_only:
        note = "Current analysis is restricted to overlapping clean dates only."
    elif start_date or end_date:
        note = "Selected date filters exclude part of the stored historical dataset."
    return HistoricalRatioOverview(
        points=points,
        summary=summary,
        data_note=(
            "Historical values below are based on locally stored sample data in SQLite. "
            "No live market data is used yet."
        ),
        metadata=HistoricalAnalysisMetadata(
            filters=filters,
            gold_row_count=len(gold_history),
            silver_row_count=len(silver_history),
            gold_distinct_dates=len({point.recorded_on for point in gold_history}),
            silver_distinct_dates=len({point.recorded_on for point in silver_history}),
            overlap_date_count=len(overlap_dates),
            effective_start_date=summary.effective_start_date if summary else None,
            effective_end_date=summary.effective_end_date if summary else None,
            note=note,
        ),
    )
