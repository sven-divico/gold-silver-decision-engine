from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models import ImportRun, PriceHistory
from app.services.data_repair import build_repair_preview, execute_repair


def _session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, class_=Session)


def test_deduplicate_preview_and_execute() -> None:
    session_factory = _session_factory()
    with session_factory() as session:
        session.add_all(
            [
                PriceHistory(recorded_on=date(2025, 1, 1), metal="gold", price_per_ounce_eur=2500),
                PriceHistory(recorded_on=date(2025, 1, 1), metal="gold", price_per_ounce_eur=2501),
                PriceHistory(recorded_on=date(2025, 1, 1), metal="silver", price_per_ounce_eur=30),
            ]
        )
        session.commit()
        preview = build_repair_preview(session, ["deduplicate"])
        result = execute_repair(session, preview, source_name="admin-data-repair")
        runs = session.query(ImportRun).all()

    assert preview.duplicate_rows_to_remove == 1
    assert result.duplicate_rows_removed == 1
    assert len(runs) == 1
    assert runs[0].source_type == "web_repair_deduplicate"


def test_prune_preview_and_execute() -> None:
    session_factory = _session_factory()
    with session_factory() as session:
        session.add_all(
            [
                PriceHistory(recorded_on=date(2025, 1, 1), metal="gold", price_per_ounce_eur=2500),
                PriceHistory(recorded_on=date(2025, 1, 2), metal="gold", price_per_ounce_eur=2510),
                PriceHistory(recorded_on=date(2025, 1, 2), metal="silver", price_per_ounce_eur=30.5),
                PriceHistory(recorded_on=date(2025, 1, 3), metal="silver", price_per_ounce_eur=31),
            ]
        )
        session.commit()
        preview = build_repair_preview(session, ["prune_non_overlap"])
        result = execute_repair(session, preview, source_name="admin-data-repair")
        remaining = session.query(PriceHistory).count()

    assert preview.non_overlap_rows_to_remove == 2
    assert result.non_overlap_rows_removed == 2
    assert remaining == 2


def test_combined_repair_creates_combined_audit_event() -> None:
    session_factory = _session_factory()
    with session_factory() as session:
        session.add_all(
            [
                PriceHistory(recorded_on=date(2025, 1, 1), metal="gold", price_per_ounce_eur=2500),
                PriceHistory(recorded_on=date(2025, 1, 1), metal="gold", price_per_ounce_eur=2501),
                PriceHistory(recorded_on=date(2025, 1, 2), metal="gold", price_per_ounce_eur=2510),
                PriceHistory(recorded_on=date(2025, 1, 1), metal="silver", price_per_ounce_eur=30),
            ]
        )
        session.commit()
        preview = build_repair_preview(session, ["deduplicate", "prune_non_overlap"])
        result = execute_repair(session, preview, source_name="admin-data-repair")
        runs = session.query(ImportRun).all()

    assert result.deleted_row_count == 2
    assert runs[0].source_type == "web_repair_combined"


def test_clean_dataset_preview_is_noop_and_execute_rejected() -> None:
    session_factory = _session_factory()
    with session_factory() as session:
        session.add_all(
            [
                PriceHistory(recorded_on=date(2025, 1, 1), metal="gold", price_per_ounce_eur=2500),
                PriceHistory(recorded_on=date(2025, 1, 1), metal="silver", price_per_ounce_eur=30),
            ]
        )
        session.commit()
        preview = build_repair_preview(session, ["deduplicate"])
        with pytest.raises(ValueError, match="would not change"):
            execute_repair(session, preview, source_name="admin-data-repair")

    assert preview.safe_to_execute is False
