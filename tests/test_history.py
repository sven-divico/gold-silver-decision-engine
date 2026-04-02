from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models import PriceHistory
from app.repositories.prices import PricePoint, SQLitePriceRepository
from app.services.history import (
    align_price_histories,
    build_historical_ratio_points,
    get_historical_ratio_overview,
    summarize_historical_ratios,
)


def test_align_price_histories_uses_shared_dates_only() -> None:
    gold = [
        PricePoint(recorded_on=date(2025, 1, 1), price_per_ounce_eur=2500),
        PricePoint(recorded_on=date(2025, 1, 2), price_per_ounce_eur=2510),
    ]
    silver = [
        PricePoint(recorded_on=date(2025, 1, 2), price_per_ounce_eur=30),
        PricePoint(recorded_on=date(2025, 1, 3), price_per_ounce_eur=31),
    ]

    aligned = align_price_histories(gold, silver)

    assert aligned == [(date(2025, 1, 2), 2510, 30)]


def test_summarize_historical_ratios_returns_expected_stats() -> None:
    points = build_historical_ratio_points(
        [
            (date(2025, 1, 1), 2400, 30),
            (date(2025, 1, 2), 2500, 31.25),
            (date(2025, 1, 3), 2600, 32.5),
        ]
    )

    summary = summarize_historical_ratios(points)

    assert summary is not None
    assert summary.latest_ratio == 80.0
    assert summary.min_ratio == 80.0
    assert summary.max_ratio == 80.0
    assert summary.average_ratio == 80.0
    assert summary.point_count == 3


def test_get_historical_ratio_overview_reads_sqlite_data() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, class_=Session)

    with session_factory() as session:
        session.add_all(
            [
                PriceHistory(recorded_on=date(2025, 1, 1), metal="gold", price_per_ounce_eur=2400),
                PriceHistory(recorded_on=date(2025, 1, 1), metal="silver", price_per_ounce_eur=30),
                PriceHistory(recorded_on=date(2025, 1, 2), metal="gold", price_per_ounce_eur=2500),
                PriceHistory(recorded_on=date(2025, 1, 2), metal="silver", price_per_ounce_eur=31.25),
            ]
        )
        session.commit()

        overview = get_historical_ratio_overview(SQLitePriceRepository(session))

    assert len(overview.points) == 2
    assert overview.summary is not None
    assert overview.summary.latest_ratio == 80.0
    assert overview.summary.min_ratio == 80.0
    assert "No live market data" in overview.data_note
