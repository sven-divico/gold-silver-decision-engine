from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import PriceHistory
from app.services.imports import record_data_event

REPAIR_ACTION_DEDUPLICATE = "deduplicate"
REPAIR_ACTION_PRUNE = "prune_non_overlap"
REPAIR_ACTIONS = {REPAIR_ACTION_DEDUPLICATE, REPAIR_ACTION_PRUNE}


@dataclass(slots=True)
class RepairWarning:
    message: str


@dataclass(slots=True)
class DuplicateRepairGroup:
    recorded_on: date
    metal: str
    kept_row_id: int
    removed_row_ids: list[int]


@dataclass(slots=True)
class RepairPreview:
    selected_actions: list[str]
    duplicate_groups: list[DuplicateRepairGroup]
    duplicate_rows_to_remove: int
    gold_only_date_count: int
    silver_only_date_count: int
    non_overlap_rows_to_remove: int
    total_rows_to_delete: int
    resulting_overlap_count: int
    safe_to_execute: bool
    warnings: list[RepairWarning]


@dataclass(slots=True)
class RepairExecutionResult:
    selected_actions: list[str]
    deleted_row_count: int
    duplicate_rows_removed: int
    non_overlap_rows_removed: int
    status: str
    summary: str


def normalize_repair_actions(actions: list[str]) -> list[str]:
    normalized = []
    for action in actions:
        value = (action or "").strip().lower()
        if value in REPAIR_ACTIONS and value not in normalized:
            normalized.append(value)
    if not normalized:
        raise ValueError("Select at least one repair action.")
    return normalized


def build_repair_preview(session: Session, actions: list[str]) -> RepairPreview:
    selected_actions = normalize_repair_actions(actions)
    duplicate_groups = _get_duplicate_groups(session) if REPAIR_ACTION_DEDUPLICATE in selected_actions else []
    duplicate_rows_to_remove = sum(len(group.removed_row_ids) for group in duplicate_groups)
    gold_only_dates, silver_only_dates = _get_non_overlapping_dates(session)
    non_overlap_rows_to_remove = 0
    if REPAIR_ACTION_PRUNE in selected_actions:
        non_overlap_rows_to_remove = _count_rows_for_dates(session, gold_only_dates | silver_only_dates)

    resulting_overlap_count = _count_resulting_overlap_dates(
        session,
        will_prune=REPAIR_ACTION_PRUNE in selected_actions,
        gold_only_dates=gold_only_dates,
        silver_only_dates=silver_only_dates,
    )
    total_rows_to_delete = duplicate_rows_to_remove + non_overlap_rows_to_remove
    warnings = _build_repair_warnings(
        selected_actions=selected_actions,
        duplicate_rows_to_remove=duplicate_rows_to_remove,
        non_overlap_rows_to_remove=non_overlap_rows_to_remove,
        resulting_overlap_count=resulting_overlap_count,
    )

    return RepairPreview(
        selected_actions=selected_actions,
        duplicate_groups=duplicate_groups[:10],
        duplicate_rows_to_remove=duplicate_rows_to_remove,
        gold_only_date_count=len(gold_only_dates),
        silver_only_date_count=len(silver_only_dates),
        non_overlap_rows_to_remove=non_overlap_rows_to_remove,
        total_rows_to_delete=total_rows_to_delete,
        resulting_overlap_count=resulting_overlap_count,
        safe_to_execute=bool(total_rows_to_delete),
        warnings=warnings,
    )


def execute_repair(
    session: Session,
    preview: RepairPreview,
    *,
    source_name: str,
) -> RepairExecutionResult:
    if not preview.safe_to_execute:
        raise ValueError("Selected repair actions would not change the dataset.")

    duplicate_rows_removed = 0
    non_overlap_rows_removed = 0

    if REPAIR_ACTION_DEDUPLICATE in preview.selected_actions:
        duplicate_row_ids = [
            row_id
            for group in _get_duplicate_groups(session)
            for row_id in group.removed_row_ids
        ]
        if duplicate_row_ids:
            duplicate_rows_removed = session.execute(
                delete(PriceHistory).where(PriceHistory.id.in_(duplicate_row_ids))
            ).rowcount or 0

    if REPAIR_ACTION_PRUNE in preview.selected_actions:
        gold_only_dates, silver_only_dates = _get_non_overlapping_dates(session)
        dates_to_remove = gold_only_dates | silver_only_dates
        if dates_to_remove:
            non_overlap_rows_removed = session.execute(
                delete(PriceHistory).where(PriceHistory.recorded_on.in_(dates_to_remove))
            ).rowcount or 0

    session.commit()
    deleted_row_count = duplicate_rows_removed + non_overlap_rows_removed
    source_type = _repair_source_type(preview.selected_actions)
    summary = (
        f"Deleted {deleted_row_count} rows: {duplicate_rows_removed} duplicate rows and "
        f"{non_overlap_rows_removed} non-overlapping rows."
    )
    record_data_event(
        session,
        source_type=source_type,
        source_name=source_name,
        import_mode="repair",
        total_rows=deleted_row_count,
        valid_rows=deleted_row_count,
        invalid_rows=0,
        imported_rows=0,
        status="success",
        notes=summary,
    )
    return RepairExecutionResult(
        selected_actions=preview.selected_actions,
        deleted_row_count=deleted_row_count,
        duplicate_rows_removed=duplicate_rows_removed,
        non_overlap_rows_removed=non_overlap_rows_removed,
        status="success",
        summary=summary,
    )


def _get_duplicate_groups(session: Session) -> list[DuplicateRepairGroup]:
    dup_stmt = (
        select(PriceHistory.recorded_on, PriceHistory.metal)
        .group_by(PriceHistory.recorded_on, PriceHistory.metal)
        .having(func.count() > 1)
        .order_by(PriceHistory.recorded_on.asc(), PriceHistory.metal.asc())
    )
    groups = []
    for recorded_on, metal in session.execute(dup_stmt).all():
        row_stmt = (
            select(PriceHistory.id)
            .where(PriceHistory.recorded_on == recorded_on, PriceHistory.metal == metal)
            .order_by(PriceHistory.id.asc())
        )
        row_ids = list(session.scalars(row_stmt).all())
        groups.append(
            DuplicateRepairGroup(
                recorded_on=recorded_on,
                metal=metal,
                kept_row_id=row_ids[0],
                removed_row_ids=row_ids[1:],
            )
        )
    return groups


def _get_non_overlapping_dates(session: Session) -> tuple[set[date], set[date]]:
    gold_dates = set(
        session.scalars(select(PriceHistory.recorded_on).where(PriceHistory.metal == "gold")).all()
    )
    silver_dates = set(
        session.scalars(select(PriceHistory.recorded_on).where(PriceHistory.metal == "silver")).all()
    )
    return gold_dates - silver_dates, silver_dates - gold_dates


def _count_rows_for_dates(session: Session, dates: set[date]) -> int:
    if not dates:
        return 0
    return session.scalar(
        select(func.count()).select_from(PriceHistory).where(PriceHistory.recorded_on.in_(dates))
    ) or 0


def _count_resulting_overlap_dates(
    session: Session,
    *,
    will_prune: bool,
    gold_only_dates: set[date],
    silver_only_dates: set[date],
) -> int:
    gold_dates = set(
        session.scalars(select(PriceHistory.recorded_on).where(PriceHistory.metal == "gold")).all()
    )
    silver_dates = set(
        session.scalars(select(PriceHistory.recorded_on).where(PriceHistory.metal == "silver")).all()
    )
    if will_prune:
        gold_dates -= gold_only_dates
        silver_dates -= silver_only_dates
    return len(gold_dates & silver_dates)


def _build_repair_warnings(
    *,
    selected_actions: list[str],
    duplicate_rows_to_remove: int,
    non_overlap_rows_to_remove: int,
    resulting_overlap_count: int,
) -> list[RepairWarning]:
    warnings: list[RepairWarning] = []
    if REPAIR_ACTION_DEDUPLICATE in selected_actions and duplicate_rows_to_remove == 0:
        warnings.append(RepairWarning("No duplicate date/metal rows were found to remove."))
    if REPAIR_ACTION_PRUNE in selected_actions and non_overlap_rows_to_remove == 0:
        warnings.append(RepairWarning("No non-overlapping rows were found to prune."))
    if resulting_overlap_count == 0:
        warnings.append(RepairWarning("No overlapping dates would remain available for ratio analysis."))
    return warnings


def _repair_source_type(selected_actions: list[str]) -> str:
    if set(selected_actions) == {REPAIR_ACTION_DEDUPLICATE, REPAIR_ACTION_PRUNE}:
        return "web_repair_combined"
    if selected_actions == [REPAIR_ACTION_DEDUPLICATE]:
        return "web_repair_deduplicate"
    return "web_repair_prune_overlap"
