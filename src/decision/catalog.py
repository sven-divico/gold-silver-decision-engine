from __future__ import annotations

import json
from pathlib import Path

from src.decision.models import (
    HYPOTHESIS_CATALOG_FILENAME,
    HYPOTHESIS_DISPLAY_NAMES,
    HYPOTHESIS_REASON_CODES,
    HypothesisDefinition,
)
from src.utils.paths import hypotheses_data_dir


def load_hypothesis_catalog(
    hypothesis_ids: list[str],
    catalog_path: str | Path | None = None,
) -> dict[str, HypothesisDefinition]:
    overrides = _load_catalog_overrides(catalog_path)
    catalog: dict[str, HypothesisDefinition] = {}
    for hypothesis_id in hypothesis_ids:
        override = overrides.get(hypothesis_id, {})
        display_name = str(
            override.get("display_name")
            or HYPOTHESIS_DISPLAY_NAMES.get(hypothesis_id)
            or hypothesis_id.replace("_", " ").title()
        )
        reason_codes = _reason_codes_for(hypothesis_id, override)
        catalog[hypothesis_id] = HypothesisDefinition(
            hypothesis_id=hypothesis_id,
            display_name=display_name,
            reason_codes=reason_codes,
        )
    return catalog


def _load_catalog_overrides(catalog_path: str | Path | None) -> dict:
    path = Path(catalog_path or (hypotheses_data_dir() / HYPOTHESIS_CATALOG_FILENAME))
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _reason_codes_for(hypothesis_id: str, override: dict) -> dict[int, str]:
    reason_codes: dict[int, str] = {}
    defaults = HYPOTHESIS_REASON_CODES.get(hypothesis_id, {})
    for key, value in defaults.items():
        reason_codes[int(key)] = str(value)

    override_codes = override.get("reason_codes", {})
    for key, value in override_codes.items():
        reason_codes[int(key)] = str(value)

    if 1 not in reason_codes:
        reason_codes[1] = "bullish_signal"
    if -1 not in reason_codes:
        reason_codes[-1] = "bearish_signal"
    return reason_codes
