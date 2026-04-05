from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.services.decision_view import load_decision_dashboard


def test_load_decision_dashboard_warns_on_missing_artifacts(tmp_path: Path) -> None:
    dashboard = load_decision_dashboard(base_dir=tmp_path)

    assert dashboard.recommendation is None
    assert any("missing" in warning.lower() for warning in dashboard.warnings)


def test_load_decision_dashboard_warns_on_stale_or_mismatched_artifacts(tmp_path: Path) -> None:
    generated_at = (datetime.now(timezone.utc) - timedelta(days=10)).replace(microsecond=0).isoformat()
    (tmp_path / "current_recommendation.json").write_text(
        json.dumps(
            {
                "date": "2025-01-01",
                "recommendation": "HOLD",
                "decision_score": 0.0,
                "confidence": 0.0,
                "active_hypotheses": 0,
                "supporting_hypotheses": [],
                "opposing_hypotheses": [],
                "summary_text": "Hold signal due to no active directional hypotheses.",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "leaderboard.json").write_text("[]", encoding="utf-8")
    (tmp_path / "decision_report.json").write_text(
        json.dumps(
            {
                "artifact_metadata": {
                    "schema_version": "decision.v0",
                    "generated_at_utc": generated_at,
                },
                "warnings": ["Custom warning"],
            }
        ),
        encoding="utf-8",
    )

    dashboard = load_decision_dashboard(base_dir=tmp_path)

    text = " ".join(dashboard.warnings).lower()
    assert "schema mismatch" in text
    assert "older than" in text
    assert "stale" in text
    assert "custom warning" in text
