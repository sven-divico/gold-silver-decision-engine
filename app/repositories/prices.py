from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.prices import SUPPORTED_METALS
from app.models import PriceHistory
from app.services.imports import build_import_preview, execute_import_with_audit, record_failed_import_attempt


@dataclass(slots=True)
class PricePoint:
    recorded_on: date
    price_per_ounce_eur: float
    row_id: int | None = None


class HistoricalPriceRepository(Protocol):
    def get_prices(
        self,
        metal: str,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[PricePoint]:
        ...

    def get_prices_for_metals(
        self,
        metals: list[str],
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, list[PricePoint]]:
        ...


class SQLitePriceRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_prices(
        self,
        metal: str,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[PricePoint]:
        _validate_metal(metal)
        stmt = select(PriceHistory).where(PriceHistory.metal == metal)
        if start_date is not None:
            stmt = stmt.where(PriceHistory.recorded_on >= start_date)
        if end_date is not None:
            stmt = stmt.where(PriceHistory.recorded_on <= end_date)
        stmt = stmt.order_by(PriceHistory.recorded_on.asc())
        rows = self.session.scalars(stmt).all()
        return [
            PricePoint(
                recorded_on=row.recorded_on,
                price_per_ounce_eur=row.price_per_ounce_eur,
                row_id=row.id,
            )
            for row in rows
        ]

    def get_prices_for_metals(
        self,
        metals: list[str],
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, list[PricePoint]]:
        return {
            metal: self.get_prices(metal, start_date=start_date, end_date=end_date) for metal in metals
        }


def import_prices_from_csv(
    session: Session,
    csv_path: Path,
    *,
    replace_existing: bool = False,
) -> int:
    if not csv_path.exists():
        raise ValueError(f"CSV file not found: {csv_path}")
    mode = "replace" if replace_existing else "append"
    try:
        csv_text = csv_path.read_text(encoding="utf-8")
        preview = build_import_preview(csv_text, mode)
    except ValueError as exc:
        record_failed_import_attempt(
            session,
            source_type="cli_csv",
            source_name=csv_path.name,
            import_mode=mode,
            error_summary=str(exc),
        )
        raise
    result = execute_import_with_audit(
        session,
        preview,
        source_type="cli_csv",
        source_name=csv_path.name,
    )
    return result.imported_rows


def _validate_metal(metal: str) -> None:
    if metal not in SUPPORTED_METALS:
        raise ValueError(f"Unsupported metal '{metal}'. Expected one of: gold, silver.")
