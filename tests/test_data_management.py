from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models import ImportRun, PriceHistory
from app.services.data_management import (
    build_sample_price_history_rows,
    get_dataset_summary,
    reseed_historical_data,
    reset_historical_data,
)


def test_dataset_summary_handles_empty_state() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, class_=Session)

    with session_factory() as session:
        summary = get_dataset_summary(session)

    assert summary.total_rows == 0
    assert summary.counts_by_metal == []
    assert summary.earliest_date is None
    assert summary.latest_date is None
    assert summary.distinct_dates == 0


def test_reseed_historical_data_replaces_dataset_and_records_event() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, class_=Session)

    with session_factory() as session:
        session.add(PriceHistory(recorded_on=date(2024, 1, 1), metal="gold", price_per_ounce_eur=1))
        session.commit()
        result = reseed_historical_data(session, source_type="web_reseed", source_name="admin-data-reseed")
        summary = get_dataset_summary(session)
        runs = session.query(ImportRun).all()

    assert result.added_rows == 180
    assert summary.total_rows == 180
    assert len(runs) == 1
    assert runs[0].source_type == "web_reseed"


def test_reset_historical_data_clears_rows_and_records_event() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, class_=Session)

    with session_factory() as session:
        session.add_all(build_sample_price_history_rows()[:4])
        session.commit()
        result = reset_historical_data(session, source_type="web_reset", source_name="admin-data-reset")
        remaining = session.query(PriceHistory).count()
        runs = session.query(ImportRun).all()

    assert result.affected_rows == 4
    assert remaining == 0
    assert len(runs) == 1
    assert runs[0].source_type == "web_reset"
