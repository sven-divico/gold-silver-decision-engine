from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models import ImportRun, PriceHistory
from app.repositories.prices import SQLitePriceRepository, import_prices_from_csv


def test_sqlite_repository_returns_date_filtered_prices(tmp_path) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, class_=Session)

    with session_factory() as session:
        session.add_all(
            [
                PriceHistory(recorded_on=date(2025, 1, 1), metal="gold", price_per_ounce_eur=2400),
                PriceHistory(recorded_on=date(2025, 1, 2), metal="gold", price_per_ounce_eur=2500),
                PriceHistory(recorded_on=date(2025, 1, 1), metal="silver", price_per_ounce_eur=30),
            ]
        )
        session.commit()

        repo = SQLitePriceRepository(session)
        points = repo.get_prices("gold", start_date=date(2025, 1, 2))

    assert len(points) == 1
    assert points[0].recorded_on == date(2025, 1, 2)
    assert points[0].price_per_ounce_eur == 2500


def test_import_prices_from_csv_happy_path(tmp_path) -> None:
    csv_path = tmp_path / "prices.csv"
    csv_path.write_text(
        "date,metal,price\n2025-01-01,gold,2500\n2025-01-01,silver,30.5\n",
        encoding="utf-8",
    )
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, class_=Session)

    with session_factory() as session:
        imported_count = import_prices_from_csv(session, csv_path)
        repo = SQLitePriceRepository(session)
        prices = repo.get_prices_for_metals(["gold", "silver"])

    assert imported_count == 2
    assert len(prices["gold"]) == 1
    assert len(prices["silver"]) == 1


def test_import_prices_from_csv_rejects_invalid_header(tmp_path) -> None:
    csv_path = tmp_path / "prices.csv"
    csv_path.write_text("recorded_on,metal,price\n2025-01-01,gold,2500\n", encoding="utf-8")
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, class_=Session)

    with session_factory() as session, pytest.raises(ValueError, match="CSV header must be exactly"):
        import_prices_from_csv(session, csv_path)


def test_import_prices_from_csv_creates_success_audit_row(tmp_path) -> None:
    csv_path = tmp_path / "prices.csv"
    csv_path.write_text("date,metal,price\n2025-01-01,gold,2500\n", encoding="utf-8")
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, class_=Session)

    with session_factory() as session:
        import_prices_from_csv(session, csv_path)
        runs = session.query(ImportRun).all()

    assert len(runs) == 1
    assert runs[0].status == "success"
    assert runs[0].source_type == "cli_csv"
