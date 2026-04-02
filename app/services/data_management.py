from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import PriceHistory
from app.services.imports import get_recent_import_runs, record_data_event


@dataclass(slots=True)
class MetalRowCount:
    metal: str
    row_count: int


@dataclass(slots=True)
class HistoricalDatasetSummary:
    total_rows: int
    counts_by_metal: list[MetalRowCount]
    earliest_date: date | None
    latest_date: date | None
    distinct_dates: int


@dataclass(slots=True)
class DatasetActionResult:
    affected_rows: int
    added_rows: int
    message: str


def get_dataset_summary(session: Session) -> HistoricalDatasetSummary:
    total_rows = session.scalar(select(func.count()).select_from(PriceHistory)) or 0
    counts_stmt = (
        select(PriceHistory.metal, func.count())
        .group_by(PriceHistory.metal)
        .order_by(PriceHistory.metal.asc())
    )
    counts_by_metal = [
        MetalRowCount(metal=metal, row_count=row_count)
        for metal, row_count in session.execute(counts_stmt).all()
    ]
    earliest_date = session.scalar(select(func.min(PriceHistory.recorded_on)))
    latest_date = session.scalar(select(func.max(PriceHistory.recorded_on)))
    distinct_dates = session.scalar(select(func.count(func.distinct(PriceHistory.recorded_on)))) or 0
    return HistoricalDatasetSummary(
        total_rows=total_rows,
        counts_by_metal=counts_by_metal,
        earliest_date=earliest_date,
        latest_date=latest_date,
        distinct_dates=distinct_dates,
    )


def build_sample_price_history_rows() -> list[PriceHistory]:
    start_date = date(2025, 1, 1)
    periods = 90
    rows: list[PriceHistory] = []
    for offset in range(periods):
        day = start_date + timedelta(days=offset)
        gold_price = 2490 + offset * 4.8 + ((offset % 7) - 3) * 6.5
        silver_price = 28.4 + offset * 0.065 + ((offset % 5) - 2) * 0.24
        rows.append(
            PriceHistory(
                recorded_on=day,
                metal="gold",
                price_per_ounce_eur=round(gold_price, 2),
            )
        )
        rows.append(
            PriceHistory(
                recorded_on=day,
                metal="silver",
                price_per_ounce_eur=round(silver_price, 2),
            )
        )
    return rows


def reset_historical_data(
    session: Session,
    *,
    source_type: str,
    source_name: str,
) -> DatasetActionResult:
    affected_rows = session.query(PriceHistory).delete()
    session.commit()
    record_data_event(
        session,
        source_type=source_type,
        source_name=source_name,
        import_mode="replace",
        total_rows=affected_rows,
        valid_rows=affected_rows,
        invalid_rows=0,
        imported_rows=0,
        status="success",
        notes="Historical price dataset reset to empty.",
    )
    return DatasetActionResult(
        affected_rows=affected_rows,
        added_rows=0,
        message=f"Deleted {affected_rows} historical price rows.",
    )


def reseed_historical_data(
    session: Session,
    *,
    source_type: str,
    source_name: str,
) -> DatasetActionResult:
    removed_rows = session.query(PriceHistory).delete()
    rows = build_sample_price_history_rows()
    session.add_all(rows)
    session.commit()
    record_data_event(
        session,
        source_type=source_type,
        source_name=source_name,
        import_mode="replace",
        total_rows=len(rows),
        valid_rows=len(rows),
        invalid_rows=0,
        imported_rows=len(rows),
        status="success",
        notes=f"Removed {removed_rows} rows and reloaded deterministic sample data.",
    )
    return DatasetActionResult(
        affected_rows=removed_rows,
        added_rows=len(rows),
        message=f"Replaced {removed_rows} rows with {len(rows)} deterministic sample rows.",
    )


def get_recent_dataset_events(session: Session, limit: int = 8):
    return get_recent_import_runs(session, limit=limit)
