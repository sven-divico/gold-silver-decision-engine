from __future__ import annotations

import json
import csv
import io
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.decision.models import DECISION_SCHEMA_VERSION
from src.utils.paths import decision_data_dir


MAX_ARTIFACT_AGE_DAYS = 3


@dataclass(slots=True)
class DecisionDashboard:
    recommendation: dict[str, Any] | None
    leaderboard: list[dict[str, Any]]
    signals: list[dict[str, Any]]
    report: dict[str, Any] | None
    warnings: list[str]


def load_decision_dashboard(base_dir: str | Path | None = None) -> DecisionDashboard:
    root = Path(base_dir or decision_data_dir())
    warnings: list[str] = []

    recommendation = _load_json_if_exists(root / "current_recommendation.json")
    leaderboard = _load_json_if_exists(root / "leaderboard.json") or []
    report = _load_json_if_exists(root / "decision_report.json")
    signals = _load_current_signals(root / "current_signals.csv")

    if recommendation is None:
        warnings.append("Decision recommendation artifact is missing. Run `python -m src.decision.engine`.")
    if not leaderboard:
        warnings.append("Leaderboard artifact is missing or empty.")
    if report is None:
        warnings.append("Decision report artifact is missing.")

    warnings.extend(_freshness_warnings(recommendation, report))
    return DecisionDashboard(
        recommendation=recommendation,
        leaderboard=leaderboard,
        signals=signals,
        report=report,
        warnings=warnings,
    )


def _load_json_if_exists(path: Path) -> Any | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _load_current_signals(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return []
    reader = csv.DictReader(io.StringIO(content))
    return [dict(row) for row in reader]


def _freshness_warnings(
    recommendation: dict[str, Any] | None,
    report: dict[str, Any] | None,
) -> list[str]:
    warnings: list[str] = []
    if report is None:
        return warnings

    metadata = report.get("artifact_metadata", {})
    schema_version = metadata.get("schema_version")
    if schema_version != DECISION_SCHEMA_VERSION:
        warnings.append(
            f"Decision artifact schema mismatch (expected {DECISION_SCHEMA_VERSION}, got {schema_version or 'missing'})."
        )

    generated_at = metadata.get("generated_at_utc")
    parsed_generated_at = _parse_datetime(generated_at)
    if parsed_generated_at is None:
        warnings.append("Decision artifact generation timestamp is missing or invalid.")
    else:
        if datetime.now(timezone.utc) - parsed_generated_at > timedelta(days=MAX_ARTIFACT_AGE_DAYS):
            warnings.append(
                f"Decision artifacts are older than {MAX_ARTIFACT_AGE_DAYS} days. Re-run the decision engine."
            )

    if recommendation is not None:
        evaluation_date = _parse_date(str(recommendation.get("date", "")))
        if evaluation_date is None:
            warnings.append("Recommendation date is missing or invalid.")
        elif date.today() - evaluation_date > timedelta(days=MAX_ARTIFACT_AGE_DAYS):
            warnings.append(
                f"Recommendation date {evaluation_date.isoformat()} looks stale. Re-run data, hypotheses, and decision engines."
            )

    report_warnings = report.get("warnings", [])
    if isinstance(report_warnings, list):
        warnings.extend(str(item) for item in report_warnings)
    return warnings


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
