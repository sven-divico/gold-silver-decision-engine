from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models import PriceHistory
from app.services.data_integrity import build_dataset_integrity_report
from app.services.imports import get_dataset_status, record_data_event


def test_integrity_report_for_clean_dataset_is_ok() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, class_=Session)

    with session_factory() as session:
        session.add_all(
            [
                PriceHistory(recorded_on=date(2025, 1, 1), metal="gold", price_per_ounce_eur=2500),
                PriceHistory(recorded_on=date(2025, 1, 2), metal="gold", price_per_ounce_eur=2510),
                PriceHistory(recorded_on=date(2025, 1, 1), metal="silver", price_per_ounce_eur=30),
                PriceHistory(recorded_on=date(2025, 1, 2), metal="silver", price_per_ounce_eur=30.5),
            ]
        )
        session.commit()
        record_data_event(
            session,
            source_type="cli_seed",
            source_name="seed_sample_data.py",
            import_mode="replace",
            total_rows=4,
            valid_rows=4,
            invalid_rows=0,
            imported_rows=4,
            status="success",
        )
        report = build_dataset_integrity_report(session, dataset_status=get_dataset_status(session))

    assert report.status == "ok"
    assert report.overlap_date_count == 2
    assert report.duplicate_summary.has_duplicates is False
    assert report.warnings == []


def test_integrity_report_detects_duplicates_and_mismatch() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, class_=Session)

    with session_factory() as session:
        session.add_all(
            [
                PriceHistory(recorded_on=date(2025, 1, 1), metal="gold", price_per_ounce_eur=2500),
                PriceHistory(recorded_on=date(2025, 1, 1), metal="gold", price_per_ounce_eur=2501),
                PriceHistory(recorded_on=date(2025, 1, 2), metal="gold", price_per_ounce_eur=2510),
                PriceHistory(recorded_on=date(2025, 1, 3), metal="silver", price_per_ounce_eur=31),
            ]
        )
        session.commit()
        report = build_dataset_integrity_report(session, dataset_status=get_dataset_status(session))

    assert report.status == "error"
    assert report.duplicate_summary.has_duplicates is True
    assert report.duplicate_summary.duplicate_group_count == 1
    assert report.overlap_date_count == 0
    assert any("Coverage mismatch" in item.message for item in report.warnings)


def test_integrity_report_for_empty_dataset_is_error() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, class_=Session)

    with session_factory() as session:
        report = build_dataset_integrity_report(session, dataset_status=get_dataset_status(session))

    assert report.status == "error"
    assert any("No historical price data" in item.message for item in report.warnings)
