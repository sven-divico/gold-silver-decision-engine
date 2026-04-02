from __future__ import annotations

from dataclasses import dataclass

from app.services.data_integrity import DatasetIntegrityReport
from app.services.history import HistoricalRatioOverview
from app.services.imports import DatasetStatus


@dataclass(slots=True)
class RatioConfidenceResult:
    confidence_level: str
    short_summary: str
    reasons: list[str]
    warnings: list[str]
    overlap_count: int
    integrity_status: str
    recently_repaired: bool
    latest_dataset_event: str | None


def evaluate_ratio_confidence(
    *,
    integrity_report: DatasetIntegrityReport,
    dataset_status: DatasetStatus,
    history_overview: HistoricalRatioOverview | None = None,
) -> RatioConfidenceResult:
    latest = dataset_status.latest_import
    latest_event = latest.source_type if latest else None
    recently_repaired = latest_event in {
        "web_repair_deduplicate",
        "web_repair_prune_overlap",
        "web_repair_combined",
    }

    reasons: list[str] = []
    warnings: list[str] = []
    overlap_count = (
        history_overview.metadata.overlap_date_count if history_overview else integrity_report.overlap_date_count
    )
    overlap_only = history_overview.metadata.filters.overlap_only if history_overview else False

    # Heuristic rules:
    # - structural integrity errors or zero overlap => low confidence
    # - thin overlap or recent repairs => medium at best
    # - clean integrity with decent overlap and no duplicates => high
    if overlap_count == 0:
        confidence_level = "low"
        reasons.append("No usable overlapping dates remain in the selected analysis view.")
    elif integrity_report.status == "error" and not overlap_only:
        confidence_level = "low"
        reasons.append("The dataset currently has structural integrity errors.")
    elif overlap_count < 10:
        confidence_level = "low"
        reasons.append("There are too few overlapping dates for a meaningful ratio history.")
    elif integrity_report.status == "warning" and not overlap_only:
        confidence_level = "medium"
        reasons.append("The dataset is usable, but integrity warnings suggest caution.")
    else:
        confidence_level = "high"
        reasons.append("The selected analysis view has overlapping gold and silver coverage.")

    if integrity_report.duplicate_summary.has_duplicates and not overlap_only:
        warnings.append("Duplicate date/metal rows are present.")
        if confidence_level == "high":
            confidence_level = "medium"

    if (integrity_report.gold_only_date_count or integrity_report.silver_only_date_count) and not overlap_only:
        warnings.append("Coverage mismatch exists between gold and silver dates.")
        if confidence_level == "high":
            confidence_level = "medium"

    if recently_repaired:
        warnings.append("The dataset was recently repaired, so recent outputs should be reviewed cautiously.")
        if confidence_level == "high":
            confidence_level = "medium"

    if history_overview and history_overview.metadata.note:
        warnings.append(history_overview.metadata.note)

    if confidence_level == "high":
        summary = "High confidence: overlapping gold and silver coverage appears structurally sound."
    elif confidence_level == "medium":
        summary = "Medium confidence: ratio history is usable, but dataset quality signals suggest caution."
    else:
        summary = "Low confidence: the stored dataset is currently weak for reliable historical ratio analysis."

    return RatioConfidenceResult(
        confidence_level=confidence_level,
        short_summary=summary,
        reasons=reasons,
        warnings=warnings,
        overlap_count=overlap_count,
        integrity_status=integrity_report.status,
        recently_repaired=recently_repaired,
        latest_dataset_event=latest_event,
    )
