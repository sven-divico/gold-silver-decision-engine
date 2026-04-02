from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models import PriceHistory
from app.services.data_integrity import build_dataset_integrity_report
from app.services.history import get_historical_ratio_overview
from app.services.imports import get_dataset_status, record_data_event
from app.services.ratio_confidence import evaluate_ratio_confidence
from app.repositories.prices import SQLitePriceRepository


def _session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, class_=Session)


def test_high_confidence_for_clean_dataset() -> None:
    session_factory = _session_factory()
    with session_factory() as session:
        for day in range(20):
            session.add(PriceHistory(recorded_on=date(2025, 1, 1 + day), metal="gold", price_per_ounce_eur=2500 + day))
            session.add(PriceHistory(recorded_on=date(2025, 1, 1 + day), metal="silver", price_per_ounce_eur=30 + day * 0.1))
        session.commit()
        record_data_event(
            session,
            source_type="cli_seed",
            source_name="seed_sample_data.py",
            import_mode="replace",
            total_rows=40,
            valid_rows=40,
            invalid_rows=0,
            imported_rows=40,
            status="success",
        )
        integrity = build_dataset_integrity_report(session, dataset_status=get_dataset_status(session))
        confidence = evaluate_ratio_confidence(integrity_report=integrity, dataset_status=get_dataset_status(session))

    assert confidence.confidence_level == "high"


def test_medium_confidence_for_recently_repaired_clean_dataset() -> None:
    session_factory = _session_factory()
    with session_factory() as session:
        for day in range(20):
            session.add(PriceHistory(recorded_on=date(2025, 2, 1 + day), metal="gold", price_per_ounce_eur=2500 + day))
            session.add(PriceHistory(recorded_on=date(2025, 2, 1 + day), metal="silver", price_per_ounce_eur=30 + day * 0.1))
        session.commit()
        record_data_event(
            session,
            source_type="web_repair_combined",
            source_name="admin-data-repair",
            import_mode="repair",
            total_rows=2,
            valid_rows=2,
            invalid_rows=0,
            imported_rows=0,
            status="success",
        )
        integrity = build_dataset_integrity_report(session, dataset_status=get_dataset_status(session))
        confidence = evaluate_ratio_confidence(integrity_report=integrity, dataset_status=get_dataset_status(session))

    assert confidence.confidence_level == "medium"
    assert confidence.recently_repaired is True


def test_low_confidence_for_empty_dataset() -> None:
    session_factory = _session_factory()
    with session_factory() as session:
        integrity = build_dataset_integrity_report(session, dataset_status=get_dataset_status(session))
        confidence = evaluate_ratio_confidence(integrity_report=integrity, dataset_status=get_dataset_status(session))

    assert confidence.confidence_level == "low"
    assert "no usable overlapping dates" in " ".join(confidence.reasons).lower()


def test_filtered_view_can_lower_confidence_for_thin_window() -> None:
    session_factory = _session_factory()
    with session_factory() as session:
        for day in range(20):
            session.add(PriceHistory(recorded_on=date(2025, 1, 1 + day), metal="gold", price_per_ounce_eur=2500 + day))
            session.add(PriceHistory(recorded_on=date(2025, 1, 1 + day), metal="silver", price_per_ounce_eur=30 + day * 0.1))
        session.commit()
        dataset_status = get_dataset_status(session)
        integrity = build_dataset_integrity_report(session, dataset_status=dataset_status)
        history = get_historical_ratio_overview(
            SQLitePriceRepository(session),
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 5),
            overlap_only=True,
        )
        confidence = evaluate_ratio_confidence(
            integrity_report=integrity,
            dataset_status=dataset_status,
            history_overview=history,
        )

    assert confidence.confidence_level == "low"
