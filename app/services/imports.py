from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from io import StringIO
import csv

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.prices import SUPPORTED_METALS
from app.models import ImportRun, PriceHistory

IMPORT_MODES = {"append", "replace"}


@dataclass(slots=True)
class ImportedPriceRow:
    recorded_on: date
    metal: str
    price_per_ounce_eur: float


@dataclass(slots=True)
class ImportPreviewRow:
    line_number: int
    raw_date: str
    raw_metal: str
    raw_price: str
    parsed_row: ImportedPriceRow | None
    error: str | None


@dataclass(slots=True)
class ImportPreview:
    mode: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: list[str]
    preview_rows: list[ImportPreviewRow]
    valid_import_rows: list[ImportedPriceRow]
    date_min: date | None
    date_max: date | None
    detected_metals: list[str]
    can_import: bool


@dataclass(slots=True)
class ImportExecutionResult:
    mode: str
    imported_rows: int
    replaced_existing: bool


@dataclass(slots=True)
class ImportAuditSummary:
    id: int
    created_at: datetime
    source_type: str
    source_name: str
    import_mode: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    imported_rows: int
    status: str
    error_summary: str | None
    notes: str | None


@dataclass(slots=True)
class DatasetStatus:
    latest_import: ImportAuditSummary | None
    total_price_rows: int
    dataset_origin: str


def build_import_preview(csv_text: str, mode: str) -> ImportPreview:
    normalized_mode = validate_import_mode(mode)
    if not csv_text.strip():
        raise ValueError("Uploaded CSV file is empty.")

    reader = csv.DictReader(StringIO(csv_text))
    expected_fields = ["date", "metal", "price"]
    if reader.fieldnames != expected_fields:
        raise ValueError("CSV header must be exactly: date,metal,price")

    preview_rows: list[ImportPreviewRow] = []
    valid_rows: list[ImportedPriceRow] = []
    errors: list[str] = []

    for line_number, raw_row in enumerate(reader, start=2):
        preview_row = _parse_preview_row(raw_row, line_number)
        preview_rows.append(preview_row)
        if preview_row.parsed_row is not None:
            valid_rows.append(preview_row.parsed_row)
        if preview_row.error:
            errors.append(f"Line {line_number}: {preview_row.error}")

    if not preview_rows:
        raise ValueError("CSV file does not contain any data rows.")

    detected_metals = sorted({row.metal for row in valid_rows})
    dates = [row.recorded_on for row in valid_rows]
    return ImportPreview(
        mode=normalized_mode,
        total_rows=len(preview_rows),
        valid_rows=len(valid_rows),
        invalid_rows=len(preview_rows) - len(valid_rows),
        errors=errors,
        preview_rows=preview_rows[:12],
        valid_import_rows=valid_rows,
        date_min=min(dates) if dates else None,
        date_max=max(dates) if dates else None,
        detected_metals=detected_metals,
        can_import=bool(valid_rows) and not errors,
    )


def execute_import(session: Session, rows: list[ImportedPriceRow], mode: str) -> ImportExecutionResult:
    normalized_mode = validate_import_mode(mode)
    if not rows:
        raise ValueError("No valid rows available for import.")

    if normalized_mode == "replace":
        session.query(PriceHistory).delete()

    session.add_all(
        PriceHistory(
            recorded_on=row.recorded_on,
            metal=row.metal,
            price_per_ounce_eur=row.price_per_ounce_eur,
        )
        for row in rows
    )
    session.commit()
    return ImportExecutionResult(
        mode=normalized_mode,
        imported_rows=len(rows),
        replaced_existing=normalized_mode == "replace",
    )


def execute_import_with_audit(
    session: Session,
    preview: ImportPreview,
    *,
    source_type: str,
    source_name: str,
) -> ImportExecutionResult:
    try:
        if not preview.can_import:
            raise ValueError("Import cannot proceed until all preview rows are valid.")
        result = execute_import(session, preview.valid_import_rows, preview.mode)
    except Exception as exc:
        _record_import_run(
            session,
            source_type=source_type,
            source_name=source_name,
            import_mode=preview.mode,
            total_rows=preview.total_rows,
            valid_rows=preview.valid_rows,
            invalid_rows=preview.invalid_rows,
            imported_rows=0,
            status="failed",
            error_summary=str(exc),
        )
        raise

    _record_import_run(
        session,
        source_type=source_type,
        source_name=source_name,
        import_mode=preview.mode,
        total_rows=preview.total_rows,
        valid_rows=preview.valid_rows,
        invalid_rows=preview.invalid_rows,
        imported_rows=result.imported_rows,
        status="success",
        error_summary=None,
    )
    return result


def record_failed_import_attempt(
    session: Session,
    *,
    source_type: str,
    source_name: str,
    import_mode: str,
    error_summary: str,
    total_rows: int = 0,
    valid_rows: int = 0,
    invalid_rows: int = 0,
) -> None:
    _record_import_run(
        session,
        source_type=source_type,
        source_name=source_name,
        import_mode=import_mode,
        total_rows=total_rows,
        valid_rows=valid_rows,
        invalid_rows=invalid_rows,
        imported_rows=0,
        status="failed",
        error_summary=error_summary,
    )


def record_data_event(
    session: Session,
    *,
    source_type: str,
    source_name: str,
    import_mode: str,
    total_rows: int,
    valid_rows: int,
    invalid_rows: int,
    imported_rows: int,
    status: str,
    error_summary: str | None = None,
    notes: str | None = None,
) -> None:
    _record_import_run(
        session,
        source_type=source_type,
        source_name=source_name,
        import_mode=import_mode,
        total_rows=total_rows,
        valid_rows=valid_rows,
        invalid_rows=invalid_rows,
        imported_rows=imported_rows,
        status=status,
        error_summary=error_summary,
        notes=notes,
    )


def get_recent_import_runs(session: Session, limit: int = 10) -> list[ImportAuditSummary]:
    stmt = select(ImportRun).order_by(ImportRun.created_at.desc(), ImportRun.id.desc()).limit(limit)
    rows = session.scalars(stmt).all()
    return [_to_audit_summary(row) for row in rows]


def get_latest_import_run(session: Session) -> ImportAuditSummary | None:
    rows = get_recent_import_runs(session, limit=1)
    return rows[0] if rows else None


def get_dataset_status(session: Session) -> DatasetStatus:
    latest = get_latest_import_run(session)
    total_price_rows = session.scalar(select(func.count()).select_from(PriceHistory)) or 0
    if latest is None:
        origin = "Seeded or manually populated dataset with no recorded import runs yet."
    elif latest.source_type in {"seed", "cli_seed", "web_reseed"}:
        origin = "Current dataset was last populated by the local seed flow."
    elif latest.source_type == "web_reset":
        origin = "Current dataset was last cleared from the web data management page."
    else:
        origin = f"Current dataset was last updated via {latest.source_type}."
    return DatasetStatus(
        latest_import=latest,
        total_price_rows=total_price_rows,
        dataset_origin=origin,
    )


def validate_import_mode(mode: str) -> str:
    normalized = (mode or "").strip().lower()
    if normalized not in IMPORT_MODES:
        raise ValueError("Import mode must be either 'append' or 'replace'.")
    return normalized


def _record_import_run(
    session: Session,
    *,
    source_type: str,
    source_name: str,
    import_mode: str,
    total_rows: int,
    valid_rows: int,
    invalid_rows: int,
    imported_rows: int,
    status: str,
    error_summary: str | None,
    notes: str | None = None,
) -> None:
    session.add(
        ImportRun(
            source_type=source_type,
            source_name=source_name,
            import_mode=import_mode,
            total_rows=total_rows,
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
            imported_rows=imported_rows,
            status=status,
            error_summary=error_summary,
            notes=notes,
        )
    )
    session.commit()


def _to_audit_summary(row: ImportRun) -> ImportAuditSummary:
    return ImportAuditSummary(
        id=row.id,
        created_at=row.created_at,
        source_type=row.source_type,
        source_name=row.source_name,
        import_mode=row.import_mode,
        total_rows=row.total_rows,
        valid_rows=row.valid_rows,
        invalid_rows=row.invalid_rows,
        imported_rows=row.imported_rows,
        status=row.status,
        error_summary=row.error_summary,
        notes=row.notes,
    )


def _parse_preview_row(raw_row: dict[str, str | None], line_number: int) -> ImportPreviewRow:
    raw_date = (raw_row.get("date") or "").strip()
    raw_metal = (raw_row.get("metal") or "").strip()
    raw_price = (raw_row.get("price") or "").strip()

    try:
        recorded_on = date.fromisoformat(raw_date)
    except ValueError:
        return ImportPreviewRow(line_number, raw_date, raw_metal, raw_price, None, "Invalid ISO date.")

    metal = raw_metal.lower()
    if metal not in SUPPORTED_METALS:
        return ImportPreviewRow(
            line_number,
            raw_date,
            raw_metal,
            raw_price,
            None,
            "Unsupported metal. Use gold or silver.",
        )

    try:
        price = float(raw_price)
    except ValueError:
        return ImportPreviewRow(line_number, raw_date, raw_metal, raw_price, None, "Price must be numeric.")

    if price <= 0:
        return ImportPreviewRow(
            line_number,
            raw_date,
            raw_metal,
            raw_price,
            None,
            "Price must be positive.",
        )

    return ImportPreviewRow(
        line_number=line_number,
        raw_date=raw_date,
        raw_metal=raw_metal,
        raw_price=raw_price,
        parsed_row=ImportedPriceRow(
            recorded_on=recorded_on,
            metal=metal,
            price_per_ounce_eur=round(price, 2),
        ),
        error=None,
    )
