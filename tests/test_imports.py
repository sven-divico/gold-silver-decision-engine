from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models import ImportRun, PriceHistory
from app.services.imports import (
    build_import_preview,
    execute_import,
    execute_import_with_audit,
    get_dataset_status,
    get_recent_import_runs,
)


def test_build_import_preview_happy_path() -> None:
    preview = build_import_preview(
        "date,metal,price\n2025-01-01,gold,2500\n2025-01-01,silver,30.5\n",
        "append",
    )

    assert preview.total_rows == 2
    assert preview.valid_rows == 2
    assert preview.invalid_rows == 0
    assert preview.can_import is True
    assert preview.detected_metals == ["gold", "silver"]
    assert preview.date_min == date(2025, 1, 1)
    assert preview.date_max == date(2025, 1, 1)


def test_build_import_preview_reports_mixed_valid_invalid_rows() -> None:
    preview = build_import_preview(
        "date,metal,price\n2025-01-01,gold,2500\n2025-01-02,platinum,99\n2025-01-03,silver,-1\n",
        "append",
    )

    assert preview.total_rows == 3
    assert preview.valid_rows == 1
    assert preview.invalid_rows == 2
    assert preview.can_import is False
    assert len(preview.errors) == 2


def test_execute_import_append_and_replace_behaviors() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, class_=Session)

    preview_one = build_import_preview("date,metal,price\n2025-01-01,gold,2500\n", "append")
    preview_two = build_import_preview("date,metal,price\n2025-01-02,silver,31\n", "append")
    preview_replace = build_import_preview("date,metal,price\n2025-01-03,gold,2600\n", "replace")

    with session_factory() as session:
        execute_import(session, preview_one.valid_import_rows, preview_one.mode)
        execute_import(session, preview_two.valid_import_rows, preview_two.mode)
        assert session.query(PriceHistory).count() == 2

        result = execute_import(session, preview_replace.valid_import_rows, preview_replace.mode)
        assert result.replaced_existing is True
        assert session.query(PriceHistory).count() == 1


def test_build_import_preview_rejects_invalid_header() -> None:
    with pytest.raises(ValueError, match="CSV header must be exactly"):
        build_import_preview("recorded_on,metal,price\n2025-01-01,gold,2500\n", "append")


def test_execute_import_with_audit_persists_success_run() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, class_=Session)
    preview = build_import_preview("date,metal,price\n2025-01-01,gold,2500\n", "append")

    with session_factory() as session:
        result = execute_import_with_audit(
            session,
            preview,
            source_type="web_csv",
            source_name="prices.csv",
        )
        runs = session.query(ImportRun).all()

    assert result.imported_rows == 1
    assert len(runs) == 1
    assert runs[0].status == "success"
    assert runs[0].source_name == "prices.csv"


def test_get_recent_import_runs_returns_newest_first() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, class_=Session)

    with session_factory() as session:
        for name in ["first.csv", "second.csv"]:
            preview = build_import_preview("date,metal,price\n2025-01-01,gold,2500\n", "append")
            execute_import_with_audit(session, preview, source_type="cli_csv", source_name=name)
        recent = get_recent_import_runs(session, limit=2)
        status = get_dataset_status(session)

    assert recent[0].source_name == "second.csv"
    assert recent[1].source_name == "first.csv"
    assert status.latest_import is not None
    assert status.total_price_rows == 2
