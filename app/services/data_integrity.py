from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import PriceHistory
from app.services.imports import DatasetStatus


@dataclass(slots=True)
class IntegrityWarning:
    level: str
    message: str


@dataclass(slots=True)
class MetalCoverageSummary:
    metal: str
    earliest_date: date | None
    latest_date: date | None
    row_count: int
    distinct_dates: int


@dataclass(slots=True)
class DuplicateSummary:
    has_duplicates: bool
    duplicate_group_count: int
    sample_groups: list[str]


@dataclass(slots=True)
class ProvenanceSummary:
    latest_event_type: str | None
    latest_source_name: str | None
    latest_import_mode: str | None
    dataset_origin: str


@dataclass(slots=True)
class DatasetIntegrityReport:
    status: str
    warnings: list[IntegrityWarning]
    per_metal_coverage: list[MetalCoverageSummary]
    overlap_date_count: int
    gold_only_date_count: int
    silver_only_date_count: int
    duplicate_summary: DuplicateSummary
    provenance: ProvenanceSummary


def build_dataset_integrity_report(
    session: Session,
    *,
    dataset_status: DatasetStatus,
) -> DatasetIntegrityReport:
    coverage = _get_per_metal_coverage(session)
    gold_dates = _get_dates_for_metal(session, "gold")
    silver_dates = _get_dates_for_metal(session, "silver")
    overlap_dates = gold_dates & silver_dates
    gold_only_dates = gold_dates - silver_dates
    silver_only_dates = silver_dates - gold_dates
    duplicate_summary = _get_duplicate_summary(session)
    warnings = _build_warnings(
        coverage=coverage,
        overlap_date_count=len(overlap_dates),
        duplicate_summary=duplicate_summary,
        gold_only_date_count=len(gold_only_dates),
        silver_only_date_count=len(silver_only_dates),
    )
    status = _classify_status(warnings)
    latest = dataset_status.latest_import
    provenance = ProvenanceSummary(
        latest_event_type=latest.source_type if latest else None,
        latest_source_name=latest.source_name if latest else None,
        latest_import_mode=latest.import_mode if latest else None,
        dataset_origin=dataset_status.dataset_origin,
    )
    return DatasetIntegrityReport(
        status=status,
        warnings=warnings,
        per_metal_coverage=coverage,
        overlap_date_count=len(overlap_dates),
        gold_only_date_count=len(gold_only_dates),
        silver_only_date_count=len(silver_only_dates),
        duplicate_summary=duplicate_summary,
        provenance=provenance,
    )


def _get_per_metal_coverage(session: Session) -> list[MetalCoverageSummary]:
    stmt = (
        select(
            PriceHistory.metal,
            func.min(PriceHistory.recorded_on),
            func.max(PriceHistory.recorded_on),
            func.count(),
            func.count(func.distinct(PriceHistory.recorded_on)),
        )
        .group_by(PriceHistory.metal)
        .order_by(PriceHistory.metal.asc())
    )
    return [
        MetalCoverageSummary(
            metal=metal,
            earliest_date=earliest_date,
            latest_date=latest_date,
            row_count=row_count,
            distinct_dates=distinct_dates,
        )
        for metal, earliest_date, latest_date, row_count, distinct_dates in session.execute(stmt).all()
    ]


def _get_dates_for_metal(session: Session, metal: str) -> set[date]:
    stmt = select(PriceHistory.recorded_on).where(PriceHistory.metal == metal)
    return set(session.scalars(stmt).all())


def _get_duplicate_summary(session: Session) -> DuplicateSummary:
    stmt = (
        select(PriceHistory.recorded_on, PriceHistory.metal, func.count().label("row_count"))
        .group_by(PriceHistory.recorded_on, PriceHistory.metal)
        .having(func.count() > 1)
        .order_by(PriceHistory.recorded_on.asc(), PriceHistory.metal.asc())
    )
    rows = session.execute(stmt).all()
    return DuplicateSummary(
        has_duplicates=bool(rows),
        duplicate_group_count=len(rows),
        sample_groups=[
            f"{recorded_on.isoformat()} / {metal} ({row_count} rows)" for recorded_on, metal, row_count in rows[:5]
        ],
    )


def _build_warnings(
    *,
    coverage: list[MetalCoverageSummary],
    overlap_date_count: int,
    duplicate_summary: DuplicateSummary,
    gold_only_date_count: int,
    silver_only_date_count: int,
) -> list[IntegrityWarning]:
    warnings: list[IntegrityWarning] = []
    if not coverage:
        warnings.append(IntegrityWarning(level="error", message="No historical price data is stored."))
        return warnings

    metals_present = {item.metal for item in coverage}
    if metals_present != {"gold", "silver"}:
        warnings.append(
            IntegrityWarning(level="error", message="Both gold and silver data are required for ratio analysis.")
        )
    if overlap_date_count == 0:
        warnings.append(
            IntegrityWarning(level="error", message="No overlapping dates exist between gold and silver series.")
        )
    if duplicate_summary.has_duplicates:
        warnings.append(
            IntegrityWarning(level="warning", message="Duplicate date/metal rows exist in the historical dataset.")
        )
    if gold_only_date_count or silver_only_date_count:
        warnings.append(
            IntegrityWarning(
                level="warning",
                message=(
                    f"Coverage mismatch detected: {gold_only_date_count} gold-only dates and "
                    f"{silver_only_date_count} silver-only dates."
                ),
            )
        )
    if len(coverage) == 2:
        counts = {item.metal: item.row_count for item in coverage}
        larger = max(counts.values())
        smaller = min(counts.values())
        if larger > 0 and smaller / larger < 0.8:
            warnings.append(
                IntegrityWarning(
                    level="warning",
                    message="One metal has materially fewer rows than the other.",
                )
            )
    return warnings


def _classify_status(warnings: list[IntegrityWarning]) -> str:
    if any(item.level == "error" for item in warnings):
        return "error"
    if warnings:
        return "warning"
    return "ok"
